from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from lemarche.conversations.models import EmailGroup
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

    @patch("lemarche.utils.apis.api_brevo.update_contact_email_blacklisted")
    def test_form_submission_updates_preferences_with_marketing_disabled(self, mock_update_contact):
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
        mock_update_contact.assert_called_once_with(self.user.email, True)

        self.assertContains(response, "Vos préférences de notifications ont été mises à jour.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.disabled_emails.count(), 1)
        self.assertIsNotNone(self.user.disabled_emails.get(group=self.email_group_2))

    @patch("lemarche.utils.apis.api_brevo.update_contact_email_blacklisted")
    def test_form_submission_updates_preferences_with_marketing_enabled(self, mock_update_contact):
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
        mock_update_contact.assert_called_once_with(self.user.email, False)

        self.assertContains(response, "Vos préférences de notifications ont été mises à jour.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.disabled_emails.count(), 0)
