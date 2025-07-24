from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from lemarche.companies.factories import CompanyFactory
from lemarche.conversations.models import EmailGroup
from lemarche.purchases.factories import PurchaseFactory
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class DashboardHomeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_with_api_token = UserFactory(kind=User.KIND_BUYER, api_key="admin")
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)

    def test_anonymous_user_cannot_access_profile(self):
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/profil/")

    def test_user_can_access_profile(self):
        self.client.force_login(self.user)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_buyer_should_display_custom_dashboard(self):
        self.client.force_login(self.user_buyer)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mes besoins")
        self.assertContains(response, "M'informer sur le marché")
        self.assertContains(response, "Annuaire des facilitateurs")
        self.assertContains(response, "Valoriser mes achats")
        self.assertContains(response, "API")
        self.assertContains(response, "M'informer sur les achats inclusifs")
        self.assertContains(response, "Ma part d'achat inclusif")
        self.assertNotContains(response, "Ajouter une structure")

    def test_user_siae_should_display_custom_dashboard(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ajouter une structure")
        self.assertContains(response, "Vos opportunités commerciales")
        self.assertContains(response, "Solutions et ressources")
        self.assertContains(response, "Aides-territoires")
        self.assertNotContains(response, "Mes besoins")
        self.assertNotContains(response, "Ma part d'achat inclusif")
        # self.assertNotContains(response, "API")

    def test_user_has_api_key_should_see_api_token(self):
        self.client.force_login(self.user_buyer_with_api_token)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Votre token")

    def test_viewing_dashboard_should_update_stats(self):
        self.assertIsNone(self.user.dashboard_last_seen_date)
        self.client.force_login(self.user)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(id=self.user.id).dashboard_last_seen_date)


class InclusivePurchaseStatsDashboardViewTest(TestCase):
    def setUp(self):
        company = CompanyFactory()
        self.user = UserFactory(kind=User.KIND_BUYER, company=company)
        self.url = reverse("dashboard:inclusive_purchase_stats")

    def test_user_siae_should_not_see_stats(self):
        user_siae = UserFactory(kind=User.KIND_SIAE)
        self.client.force_login(user_siae)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cette page est réservée aux acheteurs ayant une entreprise associée.")

    def test_user_without_company_should_not_see_stats(self):
        user_without_company = UserFactory(kind=User.KIND_BUYER)
        self.client.force_login(user_without_company)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cette page est réservée aux acheteurs ayant une entreprise associée.")

    def test_view_without_purchases_should_not_display_stats(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vous n'avez pas encore communiqué vos achats.")

    def test_view_should_display_stats_with_inclusive_purchases(self):
        self.client.force_login(self.user)

        # Create a purchase
        PurchaseFactory(company=self.user.company, siae=None, purchase_amount=10000)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ma part d'achat inclusif")
        self.assertContains(response, "<strong>10\xa0000 €</strong> d'achats réalisés")
        self.assertContains(response, "<strong>0 €</strong> d'achats inclusifs")
        self.assertContains(response, "<strong>0,0%</strong> de vos achats sont inclusifs")

    def test_view_should_display_stats_with_inclusive_purchases_only_insertion(self):
        self.client.force_login(self.user)
        PurchaseFactory(company=self.user.company, siae=None, purchase_amount=10000)
        PurchaseFactory(company=self.user.company, siae__kind=KIND_INSERTION_LIST[0], purchase_amount=20000)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ma part d'achat inclusif")
        self.assertContains(response, "<strong>30\xa0000 €</strong> d'achats réalisés")
        self.assertContains(response, "<strong>20\xa0000 €</strong> d'achats inclusifs")
        self.assertContains(response, "<strong>66,7%</strong> de vos achats sont inclusifs")
        self.assertContains(
            response,
            "<strong>1</strong> fournisseur sur les <strong>2</strong> fournisseurs référencés sont inclusifs",
        )

    def test_view_should_display_stats_with_inclusive_purchases_only_handicap(self):
        self.client.force_login(self.user)
        PurchaseFactory(company=self.user.company, siae=None, purchase_amount=10000)
        PurchaseFactory(company=self.user.company, siae__kind=KIND_HANDICAP_LIST[0], purchase_amount=20000)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ma part d'achat inclusif")
        self.assertContains(response, "<strong>30\xa0000 €</strong> d'achats réalisés")
        self.assertContains(response, "<strong>20\xa0000 €</strong> d'achats inclusifs")
        self.assertContains(response, "<strong>66,7%</strong> de vos achats sont inclusifs")
        self.assertContains(
            response,
            "<strong>1</strong> fournisseur sur les <strong>2</strong> fournisseurs référencés sont inclusifs",
        )

    def test_view_should_display_stats_with_inclusive_purchases_insertion_and_handicap(self):
        self.client.force_login(self.user)
        PurchaseFactory(company=self.user.company, siae=None, purchase_amount=10000)
        PurchaseFactory(company=self.user.company, siae__kind=KIND_INSERTION_LIST[0], purchase_amount=20000)
        PurchaseFactory(company=self.user.company, siae__kind=KIND_HANDICAP_LIST[0], purchase_amount=30000)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ma part d'achat inclusif")
        self.assertContains(response, "<strong>60\xa0000 €</strong> d'achats réalisés")
        self.assertContains(response, "<strong>50\xa0000 €</strong> d'achats inclusifs")
        self.assertContains(response, "<strong>83,3%</strong> de vos achats sont inclusifs")
        self.assertContains(
            response,
            "<strong>2</strong> fournisseurs sur les <strong>3</strong> fournisseurs référencés sont inclusifs",
        )


class DisabledEmailEditViewTest(TestCase):
    def setUp(self):
        self.user = UserFactory(kind=User.KIND_BUYER)
        self.url = reverse("dashboard:notifications_edit")
        self.email_group_1 = EmailGroup.objects.get(
            relevant_user_kind=User.KIND_BUYER, display_name="Structure(s) intéressée(s)"
        )
        self.email_group_2 = EmailGroup.objects.get(
            relevant_user_kind=User.KIND_BUYER, display_name="Communication marketing"
        )

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_get_form_displays_correctly(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/disabled_email_edit.html")

        # Check that the groups are displayed and that the 2 checkboxes are checked by default
        for group in EmailGroup.objects.filter(relevant_user_kind=self.user.kind):
            self.assertContains(response, group.display_name)
            self.assertContains(response, " checked>", count=2)

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.ContactsApi")
    def test_form_submission_updates_preferences_with_marketing_disabled(self, mock_contacts_api):
        # Setup the mock
        mock_api_instance = mock_contacts_api.return_value

        self.assertEqual(self.user.disabled_emails.count(), 0)
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                f"email_group_{self.email_group_1.pk}": True,
                f"email_group_{self.email_group_2.pk}": False,
            },
            follow=True,
        )

        # Verify the API was called correctly
        mock_api_instance.update_contact.assert_called_once()
        call_args = mock_api_instance.update_contact.call_args
        self.assertEqual(call_args[1]["identifier"], self.user.email)
        self.assertEqual(call_args[1]["update_contact"].email_blacklisted, True)

        self.assertContains(response, "Vos préférences de notifications ont été mises à jour.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.disabled_emails.count(), 1)
        self.assertIsNotNone(self.user.disabled_emails.get(group=self.email_group_2))

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.ContactsApi")
    def test_form_submission_updates_preferences_with_marketing_enabled(self, mock_contacts_api):
        # Setup the mock
        mock_api_instance = mock_contacts_api.return_value

        self.assertEqual(self.user.disabled_emails.count(), 0)
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                f"email_group_{self.email_group_1.pk}": True,
                f"email_group_{self.email_group_2.pk}": True,
            },
            follow=True,
        )

        # Verify the API was called correctly
        mock_api_instance.update_contact.assert_called_once()
        call_args = mock_api_instance.update_contact.call_args
        self.assertEqual(call_args[1]["identifier"], self.user.email)
        self.assertEqual(call_args[1]["update_contact"].email_blacklisted, False)

        self.assertContains(response, "Vos préférences de notifications ont été mises à jour.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.disabled_emails.count(), 0)
