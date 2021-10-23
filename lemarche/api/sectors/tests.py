from django.test import TestCase
from django.urls import reverse

from lemarche.sectors.factories import SectorFactory
from lemarche.users.factories import UserFactory


class SectorApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SectorFactory()
        SectorFactory()
        UserFactory(api_key="admin")

    def test_should_return_sector_list(self):
        url = reverse("api:sectors-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("slug" in response.data["results"][0])
        self.assertTrue("group" in response.data["results"][0])
