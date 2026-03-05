from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from lemarche.users.constants import PARTNER_KIND_FACILITATOR
from lemarche.users.models import User
from tests.companies.factories import CompanyFactory
from tests.conversations.factories import TemplateTransactionalFactory
from tests.users.factories import UserFactory


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
