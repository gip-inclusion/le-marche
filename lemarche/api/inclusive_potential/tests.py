from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.users.factories import UserFactory


class InclusivePotentialViewTests(TestCase):
    def setUp(self):
        self.url = reverse("api:inclusive-potential")

        self.sector = SectorFactory()
        self.perimeter_department = PerimeterFactory(
            name="Paris", kind=Perimeter.KIND_DEPARTMENT, insee_code="75", region_code="11"
        )

        self.siae_1 = SiaeFactory(kind=KIND_INSERTION_LIST[0])
        self.siae_2 = SiaeFactory(kind=KIND_INSERTION_LIST[1])
        self.siae_3 = SiaeFactory(kind=KIND_HANDICAP_LIST[0])

        for siae in [self.siae_1, self.siae_2, self.siae_3]:
            self.siae_activity_1 = SiaeActivityFactory(
                siae=siae,
                sector_group=self.sector.group,
                with_zones_perimeter=True,
            )
            self.siae_activity_1.sectors.add(self.sector)
            self.siae_activity_1.locations.set([self.perimeter_department])

        self.token = "a" * 64
        UserFactory(api_key=self.token)
        self.authenticated_client = self.client_class(headers={"authorization": f"Bearer {self.token}"})

    def test_invalid_sector(self):
        """Test with an invalid sector"""
        response = self.authenticated_client.get(self.url, {"sector": "secteur-invalide"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_perimeter(self):
        """Test with an invalid perimeter"""
        response = self.authenticated_client.get(
            self.url, {"sector": self.sector.slug, "perimeter": "perimetre-invalide"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_with_sector_and_perimeter(self):
        """Test with valid sector and perimeter"""

        response = self.authenticated_client.get(
            self.url, {"sector": self.sector.slug, "perimeter": self.perimeter_department.slug}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sector_name"], self.sector.name)
        self.assertEqual(response.data["perimeter_name"], self.perimeter_department.name)
        self.assertEqual(response.data["perimeter_kind"], self.perimeter_department.kind)
        self.assertEqual(response.data["potential_siaes"], 3)
        self.assertEqual(response.data["insertion_siaes"], 2)
        self.assertEqual(response.data["handicap_siaes"], 1)

    def test_with_sector_only(self):
        """Test with only a valid sector (without perimeter)"""

        response = self.authenticated_client.get(self.url, {"sector": self.sector.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sector_name"], self.sector.name)
        self.assertEqual(response.data["perimeter_name"], None)
        self.assertEqual(response.data["perimeter_kind"], None)
        self.assertEqual(response.data["potential_siaes"], 3)
        self.assertEqual(response.data["insertion_siaes"], 2)
        self.assertEqual(response.data["handicap_siaes"], 1)
