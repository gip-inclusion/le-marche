from django.test import TestCase
from django.urls import reverse

from tests.networks.factories import NetworkFactory
from tests.users.factories import UserFactory


class NetworkApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        NetworkFactory(name="Reseau 1")
        NetworkFactory(name="Reseau 2")
        cls.token = "a" * 64
        UserFactory(api_key=cls.token)

    def test_should_return_network_list(self):
        url = reverse("api:networks-list")
        response = self.client.get(url, headers={"authorization": f"Bearer {self.token}"})
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("slug" in response.data["results"][0])
