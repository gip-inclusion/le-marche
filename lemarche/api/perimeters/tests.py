from django.test import TestCase
from django.urls import reverse


class PerimeterChoicesApiTest(TestCase):
    def test_should_return_perimeter_kinds(self):
        url = reverse("api:perimeter-kinds-list")
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
