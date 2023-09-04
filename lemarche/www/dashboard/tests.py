from django.test import TestCase
from django.urls import reverse

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
