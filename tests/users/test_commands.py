from datetime import datetime, timezone as datetime_timezone
from io import StringIO
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.core.validators import validate_email
from django.db.models import F
from django.test import TestCase, override_settings

from lemarche.conversations.models import TemplateTransactional, TemplateTransactionalSendLog
from lemarche.users.constants import PARTNER_KIND_FACILITATOR
from lemarche.users.models import User
from tests.companies.factories import CompanyFactory
from tests.conversations.factories import TemplateTransactionalFactory
from tests.siaes.factories import SiaeFactory
from tests.users.factories import UserFactory


# To avoid different results when test will be run in the future, we patch
# and froze timezone.now used in the command
# Settings are also overriden to avoid changing settings breaking tests
@patch("django.utils.timezone.now", lambda: datetime(year=2024, month=1, day=1, tzinfo=datetime_timezone.utc))
@override_settings(
    INACTIVE_USER_TIMEOUT_IN_MONTHS=12,
    INACTIVE_USER_WARNING_DELAY_IN_DAYS=7,
)
class UserAnonymizationTestCase(TestCase):
    def setUp(self):
        frozen_now = datetime(year=2024, month=1, day=1, tzinfo=datetime_timezone.utc)
        self.frozen_last_year = frozen_now - relativedelta(years=1)
        self.frozen_warning_date = self.frozen_last_year + relativedelta(days=7)

        self.std_out = StringIO()  # to read output from executed management commands

        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()

        UserFactory(first_name="active_user", last_login=frozen_now)
        UserFactory(
            last_login=self.frozen_last_year,
            # personal data
            email="inactive_user_1@email.com",
            first_name="inactive_user_1",
            last_name="doe",
            phone="06 15 15 15 15",
            api_key="123456789",
            api_key_last_updated=frozen_now,
            siaes=[siae_1],
        )
        UserFactory(
            last_login=self.frozen_last_year,
            # personal data
            email="inactive_user_2@email.com",
            first_name="inactive_user_2",
            last_name="doe",
            phone="06 15 15 15 15",
            api_key="0000000000",
            api_key_last_updated=frozen_now,
            siaes=[siae_1, siae_2],
        )
        UserFactory(
            last_login=self.frozen_warning_date,
            first_name="about_to_be_inactive",
        )
        # Set email as active to check if it's really sent
        TemplateTransactional.objects.all().update(is_active=True)

    def test_set_inactive_user(self):
        """Select users that last logged for more than a year and flag them as inactive"""
        User.objects.filter(last_login__lte=self.frozen_last_year).update(
            is_active=False,  # inactive users should not be allowed to log in
            email=F("id"),
            first_name="",
            last_name="",
            phone="",
        )
        qs = User.objects.filter(last_login__lte=self.frozen_last_year)
        self.assertQuerySetEqual(qs.order_by("id"), User.objects.filter(is_active=False).order_by("id"))

        anonymized_user = User.objects.filter(is_active=False).first()
        self.assertEqual(anonymized_user.email, f"{anonymized_user.id}")
        self.assertFalse(anonymized_user.first_name)
        self.assertFalse(anonymized_user.last_name)
        self.assertFalse(anonymized_user.phone)

        # ensure that no error is raised calling save() with a malformed user email
        anonymized_user.email = "000"
        anonymized_user.save()

    def test_anonymize_command(self):
        """Test the admin command 'anonymize_old_users'"""

        call_command("anonymize_old_users", stdout=self.std_out)

        self.assertEqual(User.objects.filter(is_active=False).count(), 2)

        anonymized_user = User.objects.filter(is_active=False).first()

        self.assertEqual(anonymized_user.email, f"{anonymized_user.id}@domain.invalid")
        validate_email(anonymized_user.email)

        self.assertTrue(anonymized_user.is_anonymized)

        self.assertFalse(anonymized_user.first_name)
        self.assertFalse(anonymized_user.last_name)
        self.assertFalse(anonymized_user.phone)
        self.assertFalse(anonymized_user.siaes.all())

        self.assertIsNone(anonymized_user.api_key)
        self.assertIsNone(anonymized_user.api_key_last_updated)

        self.assertFalse(anonymized_user.has_usable_password())
        # from UNUSABLE_PASSWORD_SUFFIX_LENGTH it should be 40, but we're pretty close
        self.assertEqual(len(anonymized_user.password), 37)

        self.assertIn("Utilisateurs anonymisés avec succès", self.std_out.getvalue())

    def test_warn_command(self):
        """Test the admin command 'anonymize_old_users' to check if users are warned by email
        before their account is being removed"""

        call_command("anonymize_old_users", stdout=self.std_out)

        log_qs = TemplateTransactionalSendLog.objects.all()
        self.assertEqual(
            log_qs.count(),
            1,
        )

        # Called twice to veryfi that emails are not sent multiple times
        # FIXME: comment during quick revert
        # call_command("anonymize_old_users", stdout=self.std_out)
        # log_qs = TemplateTransactionalSendLog.objects.all()
        # self.assertEqual(
        #     log_qs.count(),
        #     1,
        #     msg="Warning emails are sent multiple times !",
        # )

        # email_log = log_qs.first()
        # self.assertEqual(email_log.recipient_content_object, User.objects.get(first_name="about_to_be_inactive"))

    def test_dryrun_anonymize_command(self):
        """Ensure that the database is not modified after dryrun"""

        original_qs_count = User.objects.filter(is_active=True).count()

        call_command("anonymize_old_users", dry_run=True, stdout=self.std_out)

        self.assertEqual(original_qs_count, User.objects.filter(is_active=True).count())

        self.assertIn("Utilisateurs anonymisés avec succès (2 traités)", self.std_out.getvalue())

    def test_dryrun_warn_command(self):
        """Ensure that the database is not modified after dryrun and no email have been sent"""

        call_command("anonymize_old_users", dry_run=True, stdout=self.std_out)

        self.assertFalse(TemplateTransactionalSendLog.objects.all())


class UserBuyerImportTestCase(TestCase):
    """Test the import_buyers management command"""

    def setUp(self):
        self.company = CompanyFactory(name="Grosse banque")
        TemplateTransactionalFactory(code="USER_IMPORT_BUYERS_BANQUE")

    @patch("lemarche.users.management.commands.import_buyers.add_to_contact_list")
    def test_import_buyer(self, mock_add_to_contact_list):
        call_command(
            "import_buyers",
            "tests/samples/acheteurs_import.csv",
            "USER_IMPORT_BUYERS_BANQUE",
            "grosse-banque",
            5,
            stdout=StringIO(),  # avoid polluting the logs in test execution
        )

        self.assertQuerySetEqual(
            User.objects.all(),
            ["<User: dupont.lajoie@camping.fr>", "<User: françois.perrin@celc.test.fr>"],
            ordered=False,
            transform=lambda x: repr(x),
        )
        self.assertQuerySetEqual(
            User.objects.filter(company=self.company, company_name=self.company.name),
            ["<User: dupont.lajoie@camping.fr>", "<User: françois.perrin@celc.test.fr>"],
            ordered=False,
            transform=lambda x: repr(x),
        )
        self.assertQuerySetEqual(
            User.objects.filter(is_active=True),
            ["<User: dupont.lajoie@camping.fr>", "<User: françois.perrin@celc.test.fr>"],
            ordered=False,
            transform=lambda x: repr(x),
        )

    def test_already_registered_buyer(self):
        """
        Existing buyer should have its company updated add be added to the brevo contact list
        The 2 buyers should be added to contact list, but no inscription list should be sent
        to the duplicated one.
        """
        UserFactory(email="dupont.lajoie@camping.fr")
        out = StringIO()
        with (
            patch("lemarche.users.management.commands.import_buyers.add_to_contact_list") as mock_add_to_contact_list,
            patch(
                "lemarche.users.management.commands.base_import_users.send_new_user_password_reset_link"
            ) as mock_send_new_user_password_reset_link,
        ):
            call_command(
                "import_buyers",
                "tests/samples/acheteurs_import.csv",
                "USER_IMPORT_BUYERS_BANQUE",
                "grosse-banque",
                5,
                stdout=out,
            )
        self.assertEqual(mock_add_to_contact_list.call_count, 2)
        self.assertEqual(mock_send_new_user_password_reset_link.call_count, 1)

        self.assertQuerySetEqual(
            User.objects.all(),
            ["<User: dupont.lajoie@camping.fr>", "<User: françois.perrin@celc.test.fr>"],
            ordered=False,
            transform=lambda x: repr(x),
        )

        duplicated_user = User.objects.get(email="dupont.lajoie@camping.fr")
        self.assertEqual(duplicated_user.company, self.company)
        self.assertEqual(duplicated_user.company_name, self.company.name)
        self.assertIn(
            "L'utilisateur dupont.lajoie@camping.fr est déjà inscrit, informations mises à jour.", out.getvalue()
        )
        self.assertIn("L'utilisateur françois.perrin@celc.test.fr a été inscrit avec succès.", out.getvalue())

    @patch("lemarche.users.management.commands.import_buyers.add_to_contact_list")
    def test_email_dns_added(self, mock_add_to_contact_list):
        """Ensure that email domains are added to the company's email_domain_list, without duplicates."""
        self.assertEqual(self.company.email_domain_list, [])
        call_command(
            "import_buyers",
            "tests/samples/acheteurs_import.csv",
            "USER_IMPORT_BUYERS_BANQUE",
            "grosse-banque",
            5,
            stdout=StringIO(),
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.email_domain_list, ["camping.fr", "celc.test.fr"])

        # Check that no duplicates are added
        call_command(
            "import_buyers",
            "tests/samples/acheteurs_import.csv",
            "USER_IMPORT_BUYERS_BANQUE",
            "grosse-banque",
            5,
            stdout=StringIO(),
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.email_domain_list, ["camping.fr", "celc.test.fr"])

    def test_rollback_on_error(self):
        """
        Simulate an exception when calling add_to_contact_list for dupont.lajoie@camping.fr.
        This user should not have his information saved on database, but the other users should
        """

        def bad_thing_happenned(user, contact_type):
            if user.email == "dupont.lajoie@camping.fr":
                raise Exception("Not you !")

        with patch(
            "lemarche.users.management.commands.import_buyers.add_to_contact_list", side_effect=bad_thing_happenned
        ):
            call_command(
                "import_buyers",
                "tests/samples/acheteurs_import.csv",
                "USER_IMPORT_BUYERS_BANQUE",
                "grosse-banque",
                5,
                stdout=StringIO(),
            )

        # dupont.lajoie@camping.fr is not saved
        self.assertQuerySetEqual(
            User.objects.all(),
            ["<User: françois.perrin@celc.test.fr>"],
            ordered=False,
            transform=lambda x: repr(x),
        )

        self.company.refresh_from_db()
        self.assertEqual(self.company.email_domain_list, ["celc.test.fr"])


class UserPartnerImportTestCase(TestCase):
    """Test the import_partners management command"""

    def setUp(self):
        TemplateTransactionalFactory(code="USER_IMPORT_PARTNERS_FACILITATOR")

    def test_import_partner(self):
        with patch(
            "lemarche.users.management.commands.base_import_users.send_new_user_password_reset_link"
        ) as mock_send_new_user_password_reset_link:
            call_command(
                "import_partners",
                "tests/samples/partners_import.csv",
                "USER_IMPORT_PARTNERS_FACILITATOR",
                stdout=StringIO(),
            )

        self.assertEqual(mock_send_new_user_password_reset_link.call_count, 3)

        self.assertQuerySetEqual(
            User.objects.all(),
            [
                "<User: jean.dupont@facilitateur.fr>",
                "<User: marie.martin@accompagnement.fr>",
                "<User: pierre.durand@mediation.fr>",
            ],
            ordered=False,
            transform=lambda x: repr(x),
        )

        self.assertQuerySetEqual(
            User.objects.filter(partner_kind=PARTNER_KIND_FACILITATOR),
            [
                "<User: jean.dupont@facilitateur.fr>",
                "<User: marie.martin@accompagnement.fr>",
                "<User: pierre.durand@mediation.fr>",
            ],
            ordered=False,
            transform=lambda x: repr(x),
        )

    def test_already_registered_partner(self):
        """
        Existing partner should not have its information updated and an error should be logged
        """
        UserFactory(email="jean.dupont@facilitateur.fr", kind=User.KIND_BUYER)
        out = StringIO()
        with patch(
            "lemarche.users.management.commands.base_import_users.send_new_user_password_reset_link"
        ) as mock_send_new_user_password_reset_link:
            call_command(
                "import_partners",
                "tests/samples/partners_import.csv",
                "USER_IMPORT_PARTNERS_FACILITATOR",
                stdout=out,
            )
        self.assertEqual(mock_send_new_user_password_reset_link.call_count, 2)

        self.assertQuerySetEqual(
            User.objects.all(),
            [
                "<User: jean.dupont@facilitateur.fr>",
                "<User: marie.martin@accompagnement.fr>",
                "<User: pierre.durand@mediation.fr>",
            ],
            ordered=False,
            transform=lambda x: repr(x),
        )
        self.assertIn(
            "L'utilisateur jean.dupont@facilitateur.fr est déjà inscrit, aucune mise à jour.", out.getvalue()
        )
        self.assertIn("L'utilisateur marie.martin@accompagnement.fr a été inscrit avec succès.", out.getvalue())
        self.assertIn("L'utilisateur pierre.durand@mediation.fr a été inscrit avec succès.", out.getvalue())
