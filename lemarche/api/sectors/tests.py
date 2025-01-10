from django.test import TestCase
from django.urls import reverse

from lemarche.sectors.factories import SectorFactory
from lemarche.users.factories import UserFactory


class SectorApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SectorFactory()
        SectorFactory()
        cls.token = "a" * 64
        UserFactory(api_key=cls.token)

    def test_should_return_sector_list(self):
        url = reverse("api:sectors-list")  # anonymous user
        response = self.client.get(url, headers={"authorization": f"Bearer {self.token}"})
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("slug" in response.data["results"][0])
        self.assertTrue("group" in response.data["results"][0])
