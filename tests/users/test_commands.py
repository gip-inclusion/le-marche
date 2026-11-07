import datetime
from io import StringIO
from unittest.mock import patch

from allauth.account.models import EmailAddress
from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from lemarche.conversations.models import TemplateTransactional, TemplateTransactionalSendLog
from lemarche.siaes.models import SiaeUser
from lemarche.users.constants import KIND_ADMIN, KIND_BUYER, PARTNER_KIND_FACILITATOR
from lemarche.users.models import User
from tests.companies.factories import CompanyFactory
from tests.conversations.factories import ConversationFactory, TemplateTransactionalFactory
from tests.favorites.factories import FavoriteListFactory
from tests.notes.factories import NoteFactory
from tests.sectors.factories import SectorFactory
from tests.siaes.factories import SiaeFactory, SiaeUserRequestFactory
from tests.tenders.factories import TenderFactory
from tests.users.factories import UserFactory


@freeze_time("2024-01-01")
@override_settings(
    INACTIVE_USER_TIMEOUT_IN_MONTHS=12,
)
def test_delete_old_users(db):
    frozen_now = timezone.now()
    frozen_last_year = frozen_now - relativedelta(years=1)
    frozen_warning_date = frozen_last_year + datetime.timedelta(days=30)
    pending_deletion_notice_date = frozen_now - datetime.timedelta(days=30)

    # not logged in for 'INACTIVE_USER_TIMEOUT_IN_MONTHS' months and received a notice
    # 'INACTIVE_USER_WARNING_DELAY_IN_DAYS' days ago
    user_to_delete = UserFactory(
        last_login=frozen_last_year, pending_deletion_notice_date=pending_deletion_notice_date
    )

    # not logged in for 'INACTIVE_USER_TIMEOUT_IN_MONTHS' months and received a notice
    # less than 'INACTIVE_USER_WARNING_DELAY_IN_DAYS' days ago
    warned_user = UserFactory(
        last_login=frozen_last_year,
        pending_deletion_notice_date=frozen_now - relativedelta(days=7),
    )

    # received a notice 'INACTIVE_USER_WARNING_DELAY_IN_DAYS' months ago and recently logged in
    active_warned_user = UserFactory(last_login=frozen_now, pending_deletion_notice_date=pending_deletion_notice_date)

    user_to_warn = UserFactory(last_login=frozen_warning_date)

    # active _users
    UserFactory(last_login=frozen_now)
    # never logged in but recently created user
    UserFactory(last_login=None, date_joined=frozen_now)
    # User with a recently created Tender but no recent login
    TenderFactory(author__last_login=frozen_last_year)

    # old admin to keep
    UserFactory(last_login=frozen_last_year, kind=KIND_ADMIN)

    TemplateTransactional.objects.all().update(is_active=True)

    std_out = StringIO()
    call_command("delete_old_users", dry_run=True, stdout=std_out)
    assert User.objects.count() == 8
    assert std_out.getvalue() == (
        "Dry-run: reset des utilisateurs: 1 se sont reconnectés depuis la notification\n"
        "Dry-run: avertissement des utilisateurs: 1 auraient été avertis\n"
        "Dry-run: suppression des utilisateurs: 1 auraient été supprimés\n"
    )
    # check no mail was sent
    assert TemplateTransactionalSendLog.objects.count() == 0

    std_out = StringIO()
    call_command("delete_old_users", dry_run=False, stdout=std_out)
    assert User.objects.count() == 7
    assert std_out.getvalue() == (
        "Reset des utilisateurs: 1 se sont reconnectés depuis la notification\n"
        "Avertissement des utilisateurs: 1 ont été avertis\n"
        "Suppression des utilisateurs: 1 ont été supprimés ({'users.User': 1})\n"
    )
    # check that a mail has been sent
    assert TemplateTransactionalSendLog.objects.count() == 1

    # user_to_delete was deleted
    assert not User.objects.filter(id=user_to_delete.id).exists()

    # warned_user, active_user and old_admin_to_keep are unchanged
    warned_user.refresh_from_db()
    assert warned_user.pending_deletion_notice_date == frozen_now - relativedelta(days=7)

    # a warning has been sent to user_to_warn
    user_to_warn.refresh_from_db()
    assert user_to_warn.pending_deletion_notice_date == frozen_now

    # deletion warning for active_warned_user was removed
    active_warned_user.refresh_from_db()
    assert active_warned_user.pending_deletion_notice_date is None

    # No other users were warned
    assert (
        User.objects.exclude(id__in=[warned_user.pk, user_to_warn.pk])
        .exclude(pending_deletion_notice_date=None)
        .exists()
        is False
    )

    # Called twice to verify that emails are not sent multiple times
    std_out = StringIO()
    call_command("delete_old_users", dry_run=False, stdout=std_out)
    assert User.objects.count() == 7
    assert std_out.getvalue() == (
        "Reset des utilisateurs: 0 se sont reconnectés depuis la notification\n"
        "Avertissement des utilisateurs: 0 ont été avertis\n"
        "Suppression des utilisateurs: 0 ont été supprimés\n"
    )
    # check no new mail was sent
    assert TemplateTransactionalSendLog.objects.count() == 1


@freeze_time("2024-01-15")
def test_delete_spam_users(db):
    now = timezone.now()
    old = now - relativedelta(days=7)
    recent = now - relativedelta(days=6)

    # SIAE account with no activity, unverified email, created 7+ days ago -> spam
    spam_no_email = UserFactory(created_at=old)
    spam_unverified = UserFactory(created_at=old - relativedelta(months=3))
    EmailAddress.objects.create(user=spam_unverified, email=spam_unverified.email, verified=False)
    # related objects allowed to be deleted along with the user
    NoteFactory(content_object=spam_unverified)
    TemplateTransactionalSendLog.objects.create(recipient_content_object=spam_unverified)

    kept_users = {}
    kept_users["recent"] = UserFactory(created_at=recent)
    kept_users["buyer"] = UserFactory(created_at=old, kind=KIND_BUYER)
    kept_users["verified_email"] = UserFactory(created_at=old)
    EmailAddress.objects.create(
        user=kept_users["verified_email"], email=kept_users["verified_email"].email, verified=True
    )
    kept_users["with_siae"] = UserFactory(created_at=old, siaes=[SiaeFactory()])
    kept_users["request_initiator"] = UserFactory(created_at=old)
    SiaeUserRequestFactory(initiator=kept_users["request_initiator"])
    kept_users["request_assignee"] = UserFactory(created_at=old)
    SiaeUserRequestFactory(assignee=kept_users["request_assignee"])
    # the factory makes the assignee a member of the siae: remove it to only test the request filter
    SiaeUser.objects.filter(user=kept_users["request_assignee"]).delete()
    kept_users["tender_author"] = UserFactory(created_at=old)
    TenderFactory(author=kept_users["tender_author"])
    kept_users["conversation_sender"] = UserFactory(created_at=old)
    ConversationFactory(sender_user=kept_users["conversation_sender"])
    kept_users["favorite_list"] = UserFactory(created_at=old)
    FavoriteListFactory(user=kept_users["favorite_list"])
    kept_users["with_sector"] = UserFactory(created_at=old)
    kept_users["with_sector"].sectors.add(SectorFactory())

    std_out = StringIO()
    call_command("delete_spam_users", wet_run=True, stdout=std_out)

    found_line, deleted_line = std_out.getvalue().splitlines()
    assert found_line == "Found 2 SIAE spam accounts"
    # deletion order of related models is a Django implementation detail: compare the dict, not the string
    assert deleted_line == (
        "Deleted 2 users ({'account.EmailAddress': 1, 'conversations.TemplateTransactionalSendLog': 1, "
        "'notes.Note': 1, 'users.User': 2})"
    )
    assert not User.objects.filter(id__in=[spam_no_email.id, spam_unverified.id]).exists()
    for reason, user in kept_users.items():
        assert User.objects.filter(id=user.id).exists(), f"{reason} user should not have been deleted"


@freeze_time("2024-01-15")
def test_delete_spam_users_dry_run(db):
    UserFactory(created_at=timezone.now() - relativedelta(days=30))

    std_out = StringIO()
    call_command("delete_spam_users", stdout=std_out)

    assert "Found 1 SIAE spam accounts" in std_out.getvalue()
    assert User.objects.count() == 1


@freeze_time("2024-01-15")
def test_delete_spam_users_nothing_to_delete(db):
    UserFactory(created_at=timezone.now())

    std_out = StringIO()
    call_command("delete_spam_users", wet_run=True, stdout=std_out)

    assert std_out.getvalue() == "Found 0 SIAE spam accounts\n"
    assert User.objects.count() == 1


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
            stdout=StringIO(),  # avoid polluting the logs in test execution
        )

        self.assertQuerySetEqual(
            User.objects.all(),
            [
                "<User: dupont.lajoie@camping.fr>",
                "<User: françois.perrin@celc.test.fr>",
            ],
            ordered=False,
            transform=lambda x: repr(x),
        )
        self.assertQuerySetEqual(
            User.objects.filter(company=self.company, company_name=self.company.name),
            [
                "<User: dupont.lajoie@camping.fr>",
                "<User: françois.perrin@celc.test.fr>",
            ],
            ordered=False,
            transform=lambda x: repr(x),
        )
        self.assertQuerySetEqual(
            User.objects.filter(is_active=True),
            [
                "<User: dupont.lajoie@camping.fr>",
                "<User: françois.perrin@celc.test.fr>",
            ],
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
                stdout=out,
            )
        self.assertEqual(mock_add_to_contact_list.call_count, 2)
        self.assertEqual(mock_send_new_user_password_reset_link.call_count, 1)

        self.assertQuerySetEqual(
            User.objects.all(),
            [
                "<User: dupont.lajoie@camping.fr>",
                "<User: françois.perrin@celc.test.fr>",
            ],
            ordered=False,
            transform=lambda x: repr(x),
        )

        duplicated_user = User.objects.get(email="dupont.lajoie@camping.fr")
        self.assertEqual(duplicated_user.company, self.company)
        self.assertEqual(duplicated_user.company_name, self.company.name)
        self.assertIn(
            "L'utilisateur dupont.lajoie@camping.fr est déjà inscrit, informations mises à jour.",
            out.getvalue(),
        )
        self.assertIn(
            "L'utilisateur françois.perrin@celc.test.fr a été inscrit avec succès.",
            out.getvalue(),
        )

    @patch("lemarche.users.management.commands.import_buyers.add_to_contact_list")
    def test_email_dns_added(self, mock_add_to_contact_list):
        """Ensure that email domains are added to the company's email_domain_list, without duplicates."""
        self.assertEqual(self.company.email_domain_list, [])
        call_command(
            "import_buyers",
            "tests/samples/acheteurs_import.csv",
            "USER_IMPORT_BUYERS_BANQUE",
            "grosse-banque",
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
            stdout=StringIO(),
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.email_domain_list, ["camping.fr", "celc.test.fr"])


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
            "L'utilisateur jean.dupont@facilitateur.fr est déjà inscrit, aucune mise à jour.",
            out.getvalue(),
        )
        self.assertIn(
            "L'utilisateur marie.martin@accompagnement.fr a été inscrit avec succès.",
            out.getvalue(),
        )
        self.assertIn(
            "L'utilisateur pierre.durand@mediation.fr a été inscrit avec succès.",
            out.getvalue(),
        )
