from django.test import TestCase
from django.urls import reverse

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.users.factories import UserFactory


class PerimeterListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
        )
        cls.perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.perimeter_region = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        UserFactory(api_key="admin")

    def test_should_return_perimeter_list(self):
        url = reverse("api:perimeters-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

    def test_should_filter_perimeter_list_by_kind(self):
        # single
        url = reverse("api:perimeters-list") + f"?kind={Perimeter.KIND_CITY}"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = (
            reverse("api:perimeters-list") + f"?kind={Perimeter.KIND_CITY}&kind={Perimeter.KIND_DEPARTMENT}"
        )  # anonymous user  # noqa
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)


class PerimetersAutocompleteFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
        )
        cls.perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.perimeter_region = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        UserFactory(api_key="admin")

    def test_perimeters_autocomplete_should_not_paginate(self):
        url = reverse("api:perimeters-autocomplete-list")  # anonymous user
        response = self.client.get(url)
        self.assertTrue("previous" not in response.data)
        self.assertTrue("next" not in response.data)
        self.assertTrue("count" not in response.data)

    def test_perimeters_autocomplete_should_have_q(self):
        url = reverse("api:perimeters-autocomplete-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        url = reverse("api:perimeters-autocomplete-list") + "?q="  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_should_filter_perimeters_autocomplete_by_q_name(self):
        url = reverse("api:perimeters-autocomplete-list") + "?q=grenob"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_should_filter_perimeters_autocomplete_by_q_code(self):
        url = reverse("api:perimeters-autocomplete-list") + "?q=38"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1 + 1)
        self.assertEqual(response.data[0]["name"], "Isère")

    def test_should_filter_perimeters_autocomplete_by_q_post_code(self):
        url = reverse("api:perimeters-autocomplete-list") + "?q=38100"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_should_filter_perimeters_autocomplete_by_q_post_code_incomplete_success(self):
        url = reverse("api:perimeters-autocomplete-list") + "?q=3800"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_should_filter_perimeters_autocomplete_by_q_post_code_incomplete_failure(self):
        """
        Edge case...
        This search doesn't return any results because we only filter on the
        first post_codes array item (when the post_code is incomplete)
        """
        url = reverse("api:perimeters-autocomplete-list") + "?q=3810"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)

    def test_should_filter_perimeters_autocomplete_by_result_count(self):
        url = reverse("api:perimeters-autocomplete-list") + "?results=1"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)


class PerimeterChoicesApiTest(TestCase):
    def test_should_return_perimeter_kinds_list(self):
        url = reverse("api:perimeter-kinds-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
