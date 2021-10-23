from django.test import TestCase
from django.urls import reverse

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.users.factories import UserFactory


class PerimeterListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble", kind=Perimeter.KIND_CITY, insee_code="38185", department_code="38", region_code="84"
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

    def test_should_filter_perimeter_list_by_name(self):
        url = reverse("api:perimeters-list") + "?name=grenob"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_should_filter_perimeter_list_by_result_count(self):
        url = reverse("api:perimeters-list") + "?results=1"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    # def test_perimeter_list_should_not_paginate_if_results_passed(self):
    #     url = reverse("api:perimeters-list") + "?results=1"  # anonymous user
    #     response = self.client.get(url)
    #     self.assertEqual(response.data["previous"], None)
    #     self.assertEqual(response.data["next"], None)


class PerimeterChoicesApiTest(TestCase):
    def test_should_return_perimeter_kinds_list(self):
        url = reverse("api:perimeter-kinds-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
