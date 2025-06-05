from datetime import datetime, timezone as datetime_timezone
from io import StringIO
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.core.validators import validate_email
from django.db.models import F
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from lemarche.companies.factories import CompanyFactory
from lemarche.conversations.factories import TemplateTransactionalFactory
from lemarche.conversations.models import TemplateTransactional, TemplateTransactionalSendLog
from lemarche.favorites.factories import FavoriteListFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users import constants as user_constants
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_str(self):
        user = UserFactory(email="coucou@example.com")
        self.assertEqual(str(user), "coucou@example.com")

    def test_full_name(self):
        user = UserFactory(first_name="Paul", last_name="Anploi")
        self.assertEqual(user.full_name, "Paul Anploi")

    def test_kind_detail_display(self):
        user_siae = UserFactory(kind=user_constants.KIND_SIAE)
        user_buyer = UserFactory(kind=user_constants.KIND_BUYER)
        user_buyer_public = UserFactory(kind=user_constants.KIND_BUYER, buyer_kind=user_constants.BUYER_KIND_PUBLIC)
        user_buyer_private_pme = UserFactory(
            kind=user_constants.KIND_BUYER,
            buyer_kind=user_constants.BUYER_KIND_PRIVATE,
            buyer_kind_detail=user_constants.BUYER_KIND_DETAIL_PRIVATE_PME,
        )
        user_partner = UserFactory(kind=user_constants.KIND_PARTNER)
        user_partner_facilitator = UserFactory(
            kind=user_constants.KIND_PARTNER, partner_kind=user_constants.PARTNER_KIND_FACILITATOR
        )
        self.assertEqual(user_siae.kind_detail_display, "Structure")
        self.assertEqual(user_buyer.kind_detail_display, "Acheteur")
        self.assertEqual(user_partner.kind_detail_display, "Partenaire")
        self.assertEqual(user_buyer_public.kind_detail_display, "Acheteur")
        self.assertEqual(user_buyer_private_pme.kind_detail_display, "Acheteur : PME")
        self.assertEqual(
            user_partner_facilitator.kind_detail_display, "Partenaire : Facilitateur des clauses sociales"
        )


class UserModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_is_admin_bizdev(self):
        UserFactory(kind=user_constants.KIND_ADMIN, is_staff=True)
        UserFactory(kind=user_constants.KIND_ADMIN, is_staff=True, position="BizDev")
        UserFactory(kind=user_constants.KIND_ADMIN, is_staff=True, position="Bizdev")
        self.assertEqual(User.objects.count(), 1 + 3)
        self.assertEqual(User.objects.is_admin_bizdev().count(), 2)

    def test_has_company(self):
        user_2 = UserFactory()
        CompanyFactory(users=[user_2])
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_company().count(), 1)

    def test_has_siae(self):
        user_2 = UserFactory()
        SiaeFactory(users=[user_2])
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_siae().count(), 1)

    def test_has_tender(self):
        user_2 = UserFactory()
        TenderFactory(author=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_tender().count(), 1)

    def test_has_favorite_list(self):
        user_2 = UserFactory()
        FavoriteListFactory(user=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_favorite_list().count(), 1)

    def test_has_api_key(self):
        UserFactory(api_key="coucou")
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_api_key().count(), 1)

    def test_has_email_domain(self):
        UserFactory(email="test@ain.fr")
        UserFactory(email="test@plateau-urbain.fr")
        self.assertEqual(User.objects.count(), 1 + 2)
        for EMAIL_DOMAIN in ["ain.fr", "@ain.fr"]:
            with self.subTest(email_domain=EMAIL_DOMAIN):
                self.assertEqual(User.objects.has_email_domain(email_domain=EMAIL_DOMAIN).count(), 1)

    def test_with_siae_stats(self):
        user_2 = UserFactory()
        SiaeFactory(users=[user_2])
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.with_siae_stats().filter(id=self.user.id).first().siae_count_annotated, 0)
        self.assertEqual(User.objects.with_siae_stats().filter(id=user_2.id).first().siae_count_annotated, 1)

    def test_with_tender_stats(self):
        user_2 = UserFactory()
        TenderFactory(author=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.with_tender_stats().filter(id=self.user.id).first().tender_count_annotated, 0)
        self.assertEqual(User.objects.with_tender_stats().filter(id=user_2.id).first().tender_count_annotated, 1)

    def test_chain_querysets(self):
        user_2 = UserFactory(api_key="chain")
        siae = SiaeFactory()
        siae.users.add(user_2)
        self.assertEqual(
            User.objects.has_api_key().with_siae_stats().filter(id=user_2.id).first().siae_count_annotated, 1
        )


class UserModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_update_last_updated_fields(self):
        user = UserFactory()
        self.assertIsNone(user.api_key)
        self.assertIsNone(user.api_key_last_updated)
        # new value: last_updated field will be set
        user = User.objects.get(id=user.id)  # we need to fetch it again to pass through the __init__
        user.api_key = "AZERTY"
        user.save()
        self.assertEqual(user.api_key, "AZERTY")
        self.assertIsNotNone(user.api_key_last_updated)
        api_key_last_updated = user.api_key_last_updated
        # same value: last_updated field will not be updated
        user = User.objects.get(id=user.id)
        user.api_key = "AZERTY"
        user.save()
        self.assertEqual(user.api_key, "AZERTY")
        self.assertEqual(user.api_key_last_updated, api_key_last_updated)
        # updated value: last_updated field will be updated
        user = User.objects.get(id=user.id)
        user.api_key = "QWERTY"
        user.save()
        self.assertEqual(user.api_key, "QWERTY")
        self.assertNotEqual(user.api_key_last_updated, api_key_last_updated)

    def test_update_related_favorite_list_count_on_save(self):
        user = UserFactory()
        self.assertEqual(user.favorite_list_count, 0)
        # create 2 lists
        FavoriteListFactory(user=user)
        FavoriteListFactory(user=user)
        self.assertEqual(user.favorite_lists.count(), 2)
        self.assertEqual(user.favorite_list_count, 2)
        # delete 1 list
        user.favorite_lists.first().delete()
        self.assertEqual(user.favorite_lists.count(), 1)
        self.assertEqual(user.favorite_list_count, 1)


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


class UserAdminTestCase(TestCase):
    def setUp(self):
        UserFactory(is_staff=False, is_anonymized=False)
        super_user = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(super_user)

    def test_anonymize_action(self):
        """Test the anonymize_users action from the admin"""

        users_ids = User.objects.values_list("id", flat=True)
        data = {
            "action": "anonymize_users",
            "_selected_action": users_ids,
        }
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#reversing-admin-urls
        change_url = reverse("admin:users_user_changelist")
        response = self.client.post(path=change_url, data=data)

        self.assertEqual(response.status_code, 302)

        data_confirm = {"user_id": users_ids}

        # click on confirm after seeing the confirmation page
        response_confirm = self.client.post(response.url, data=data_confirm)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(User.objects.filter(is_staff=False).first().is_anonymized)
        self.assertFalse(User.objects.filter(is_staff=True).first().is_anonymized)

        messages_strings = [str(message) for message in get_messages(response_confirm.wsgi_request)]
        self.assertIn("L'anonymisation s'est déroulée avec succès", messages_strings)


class UserBuyerImportTestCase(TransactionTestCase):
    """Test the import_buyers management command"""

    def setUp(self):
        self.company = CompanyFactory(name="Grosse banque")
        TemplateTransactionalFactory(code="NEW_COMPANY")

    def test_import_buyer(self):
        call_command(
            "import_buyers",
            "lemarche/fixtures/tests/acheteurs_bpce.csv",
            "grosse-banque",
            "NEW_COMPANY",
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
        UserFactory(email="dupont.lajoie@camping.fr")

        call_command(
            "import_buyers",
            "lemarche/fixtures/tests/acheteurs_bpce.csv",
            "grosse-banque",
            "NEW_COMPANY",
            5,
            stdout=StringIO(),
        )

        self.assertQuerySetEqual(
            User.objects.all(),
            ["<User: dupont.lajoie@camping.fr>", "<User: françois.perrin@celc.test.fr>"],
            ordered=False,
            transform=lambda x: repr(x),
        )

        duplicated_user = User.objects.get(email="dupont.lajoie@camping.fr")
        self.assertEqual(duplicated_user.company, self.company)
        self.assertEqual(duplicated_user.company_name, self.company.name)

        # todo check that contactlist is called but no inscription link is sent
