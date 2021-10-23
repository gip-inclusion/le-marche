from django.test import TestCase
from django.urls import reverse

from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory


class SiaeRetrieveBySiretApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        UserFactory(api_key="admin")

    def test_should_return_404_if_siret_unknown(self):
        url = reverse("api:siae-retrieve-by-siret", args=["123"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_should_return_404_if_siret_known_but_with_spaces(self):
        url = reverse("api:siae-retrieve-by-siret", args=["123 123 123 12345"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_should_return_siae_if_siret_known(self):
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), dict)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertTrue("slug" not in response.data)

    def test_authenticated_user_should_get_full_siae_object(self):
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"]) + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertEqual(response.data["slug"], "une-structure-38")


class SiaeChoicesApiTest(TestCase):
    def test_should_return_siae_kinds(self):
        url = reverse("api:siae-kinds-list")
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 8)
        self.assertEqual(len(response.data["results"]), 8)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])

    def test_should_return_siae_presta_types(self):
        url = reverse("api:siae-presta-types-list")
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
