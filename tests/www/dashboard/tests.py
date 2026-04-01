from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from lemarche.conversations.models import EmailGroup
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.users.models import User
from tests.companies.factories import CompanyFactory
from tests.purchases.factories import PurchaseFactory
from tests.users.factories import UserFactory


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
        self.assertEqual(response.context["total_purchases"], 10000)
        self.assertEqual(response.context["total_inclusive_purchases"], 0)
        self.assertEqual(response.context["total_inclusive_purchases_percentage"], 0)

    def test_view_should_display_stats_with_inclusive_purchases_only_insertion(self):
        self.client.force_login(self.user)
        PurchaseFactory(company=self.user.company, siae=None, purchase_amount=10000)
        PurchaseFactory(company=self.user.company, siae__kind=KIND_INSERTION_LIST[0], purchase_amount=20000)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_purchases"], 30000)
        self.assertEqual(response.context["total_inclusive_purchases"], 20000)
        self.assertEqual(response.context["total_inclusive_purchases_percentage"], 66.67)
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
        self.assertEqual(response.context["total_purchases"], 30000)
        self.assertEqual(response.context["total_inclusive_purchases"], 20000)
        self.assertEqual(response.context["total_inclusive_purchases_percentage"], 66.67)
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
        self.assertEqual(response.context["total_purchases"], 60000)
        self.assertEqual(response.context["total_inclusive_purchases"], 50000)
        self.assertEqual(response.context["total_inclusive_purchases_percentage"], 83.33)
        self.assertContains(
            response,
            "<strong>2</strong> fournisseurs sur les <strong>3</strong> fournisseurs référencés sont inclusifs",
        )

    def test_view_includes_chart_data_qpv_zrr_with_correct_segments(self):
        """chart_data_qpv_zrr has 4 segments: QPV only, ZRR only, both, neither."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__is_qpv=True,
            siae__is_zrr=False,
            purchase_amount=15000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__is_qpv=False,
            siae__is_zrr=True,
            purchase_amount=25000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__is_qpv=True,
            siae__is_zrr=True,
            purchase_amount=5000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__is_qpv=False,
            siae__is_zrr=False,
            purchase_amount=10000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data_qpv_zrr"]
        self.assertEqual(
            chart["labels"],
            ["QPV uniquement", "ZRR uniquement", "QPV et ZRR", "Ni QPV ni ZRR"],
        )
        self.assertEqual(chart["dataset"], [15000, 25000, 5000, 10000])

    def test_filter_is_qpv_restricts_to_qpv_siaes_only(self):
        """When is_qpv checkbox is checked, only purchases with siae.is_qpv=True are counted."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__is_qpv=True,
            siae__is_zrr=False,
            purchase_amount=10000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__is_qpv=False,
            siae__is_zrr=False,
            purchase_amount=20000,
        )
        response = self.client.get(self.url, {"is_qpv": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_purchases"], 10000)

    def test_filter_is_zrr_restricts_to_zrr_siaes_only(self):
        """When is_zrr checkbox is checked, only purchases with siae.is_zrr=True are counted."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__is_qpv=False,
            siae__is_zrr=True,
            purchase_amount=15000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__is_qpv=False,
            siae__is_zrr=False,
            purchase_amount=25000,
        )
        response = self.client.get(self.url, {"is_zrr": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_purchases"], 15000)

    def test_size_stats_tpe_pme_and_non_renseigne(self):
        """chart_data_size correctly splits TPE, PME and Non renseigné."""
        self.client.force_login(self.user)
        # TPE: 3 insertion + 2 permanent = 5 → < 10
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__employees_insertion_count=3,
            siae__employees_permanent_count=2,
            purchase_amount=10000,
        )
        # PME: 8 + 7 = 15 → >= 10
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__employees_insertion_count=8,
            siae__employees_permanent_count=7,
            purchase_amount=20000,
        )
        # Non renseigné: all null
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__employees_insertion_count=None,
            siae__employees_permanent_count=None,
            siae__c2_etp_count=None,
            purchase_amount=5000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data_size"]
        tpe_idx = chart["labels"].index("TPE (< 10 salariés)")
        pme_idx = chart["labels"].index("PME (≥ 10 salariés)")
        nr_idx = chart["labels"].index("Non renseigné")
        self.assertEqual(chart["amounts"][tpe_idx], 10000)
        self.assertEqual(chart["amounts"][pme_idx], 20000)
        self.assertEqual(chart["amounts"][nr_idx], 5000)
        self.assertEqual(chart["supplier_counts"][tpe_idx], 1)
        self.assertEqual(chart["supplier_counts"][pme_idx], 1)

    def test_size_stats_uses_c2_etp_count_as_fallback(self):
        """When employees_insertion_count is null, c2_etp_count is used for size classification."""
        self.client.force_login(self.user)
        # c2_etp_count=5.7 → round=6, permanent=2 → total=8 → TPE
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__employees_insertion_count=None,
            siae__c2_etp_count=5.7,
            siae__employees_permanent_count=2,
            purchase_amount=12000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data_size"]
        tpe_idx = chart["labels"].index("TPE (< 10 salariés)")
        self.assertEqual(chart["amounts"][tpe_idx], 12000)

    def test_legal_form_stats_groups_by_legal_form(self):
        """chart_data_legal_form returns labels and amounts grouped by legal form."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__legal_form="ASSOCIATION",
            purchase_amount=30000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__legal_form="SAS",
            purchase_amount=15000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data_legal_form"]
        # Association has highest amount → should be first
        self.assertIn("Association", chart["labels"])
        self.assertIn("SAS (Société par actions simplifiée)", chart["labels"])
        assoc_idx = chart["labels"].index("Association")
        self.assertEqual(chart["amounts"][assoc_idx], 30000)

    def test_legal_form_stats_blank_shows_non_renseigne(self):
        """A siae with blank legal_form is shown as 'Non renseigné'."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__legal_form="",
            purchase_amount=8000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data_legal_form"]
        self.assertIn("Non renseigné", chart["labels"])

    def test_region_stats_groups_by_region(self):
        """chart_data_region returns labels and amounts grouped by region, descending."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__region="Île-de-France",
            purchase_amount=50000,
        )
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__region="Bretagne",
            purchase_amount=20000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data_region"]
        self.assertEqual(chart["labels"][0], "Île-de-France")
        self.assertEqual(chart["amounts"][0], 50000)
        self.assertIn("Bretagne", chart["labels"])

    def test_region_stats_table_rows_include_percentage(self):
        """chart_data_region.rows contains (label, amount, pct, supplier_count) tuples."""
        self.client.force_login(self.user)
        PurchaseFactory(
            company=self.user.company,
            siae__kind=KIND_INSERTION_LIST[0],
            siae__region="Bretagne",
            purchase_amount=40000,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        rows = response.context["chart_data_region"]["rows"]
        self.assertEqual(len(rows), 1)
        label, amount, pct, count = rows[0]
        self.assertEqual(label, "Bretagne")
        self.assertEqual(amount, 40000)
        self.assertEqual(pct, 100.0)
        self.assertEqual(count, 1)


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

    @patch("lemarche.utils.apis.api_brevo.brevo_python.ContactsApi")
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

    @patch("lemarche.utils.apis.api_brevo.brevo_python.ContactsApi")
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
