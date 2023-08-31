from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from lemarche.networks.factories import NetworkFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class DashboardNetworkViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.DASHBOARD_NETWORK_URLS = [
            "dashboard_networks:detail",
            "dashboard_networks:siae_list",
            "dashboard_networks:tender_list",
            # "dashboard_networks:tender_detail"
            # "dashboard_networks:siae_tender_list"
        ]
        cls.network_1 = NetworkFactory(name="Liste 1")
        cls.network_2 = NetworkFactory(name="Liste 2")
        cls.user_network_1 = UserFactory(kind=User.KIND_PARTNER, partner_network=cls.network_1)
        cls.user_network_2 = UserFactory(kind=User.KIND_PARTNER, partner_network=cls.network_2)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_without_network = UserFactory(kind=User.KIND_PARTNER)
        cls.siae_1 = SiaeFactory(networks=[cls.network_1])
        cls.siae_2 = SiaeFactory()
        cls.tender_1 = TenderFactory(
            author=cls.user_buyer,
            status=tender_constants.STATUS_VALIDATED,
            validated_at=timezone.now(),
            deadline_date=timezone.now() - timedelta(days=5),
        )
        cls.tendersiae_1_1 = TenderSiae.objects.create(
            tender=cls.tender_1, siae=cls.siae_1, email_send_date=timezone.now()
        )
        cls.tendersiae_1_2 = TenderSiae.objects.create(
            tender=cls.tender_1, siae=cls.siae_2, email_send_date=timezone.now()
        )
        cls.tender_2 = TenderFactory()

    def test_anonymous_user_cannot_view_network_pages(self):
        for dashboard_network_url in self.DASHBOARD_NETWORK_URLS:
            url = reverse(dashboard_network_url, args=[self.network_1.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_network_member_can_access_network_pages(self):
        # non network members
        for user in [self.user_network_2, self.user_buyer, self.user_without_network]:
            self.client.force_login(user)
            for dashboard_network_url in self.DASHBOARD_NETWORK_URLS:
                url = reverse(dashboard_network_url, args=[self.network_1.slug])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, "/profil/")
        # network member
        self.client.force_login(self.user_network_1)
        for dashboard_network_url in self.DASHBOARD_NETWORK_URLS:
            url = reverse(dashboard_network_url, args=[self.network_1.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_siae_list_in_network_siae_list(self):
        self.client.force_login(self.user_network_1)
        url = reverse("dashboard_networks:siae_list", args=[self.network_1.slug])
        response = self.client.get(url)
        self.assertContains(response, self.siae_1.name_display)
        self.assertNotContains(response, self.siae_2.name_display)

    def test_only_network_siaes_can_display_network_siae_tender_list(self):
        self.client.force_login(self.user_network_1)
        url = reverse("dashboard_networks:siae_tender_list", args=[self.network_1.slug, self.siae_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tender_1.title)
        # siae_2 not linked to network
        self.client.force_login(self.user_network_1)
        url = reverse("dashboard_networks:siae_tender_list", args=[self.network_1.slug, self.siae_2.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/profil/reseaux/{self.network_1.slug}/prestataires/")

    def test_tender_list_in_network_tender_list(self):
        self.client.force_login(self.user_network_1)
        url = reverse("dashboard_networks:tender_list", args=[self.network_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tender_1.title)
        self.assertContains(response, "1 adhérent notifié")
        self.assertNotContains(response, self.tender_2.title)

    def test_tender_detail_in_network_tender_detail(self):
        self.client.force_login(self.user_network_1)
        url = reverse("dashboard_networks:tender_detail", args=[self.network_1.slug, self.tender_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tender_1.title)
        self.assertContains(response, "1 adhérent notifié")
        self.assertContains(response, "0 adhérents intéressés")
        self.assertNotContains(response, self.tender_2.title)

    def test_network_siae_list_in_network_tender_siae_list(self):
        self.client.force_login(self.user_network_1)
        url = reverse("dashboard_networks:tender_siae_list", args=[self.network_1.slug, self.tender_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.siae_1.name_display)
        self.assertNotContains(response, self.siae_2.name_display)
