from django.test import TestCase
from django.urls import reverse

from lemarche.networks.factories import NetworkFactory
from lemarche.users.factories import UserFactory


class NetworkApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        NetworkFactory()
        NetworkFactory()
        UserFactory(api_key="admin")

    def test_should_return_network_list(self):
        url = reverse("api:networks-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("slug" in response.data["results"][0])
