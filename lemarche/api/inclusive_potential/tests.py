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

        siae_1 = SiaeFactory(kind=KIND_INSERTION_LIST[0], api_entreprise_ca=200000)
        siae_2 = SiaeFactory(kind=KIND_INSERTION_LIST[1], super_badge=True, ca=1000000, api_entreprise_ca=500000)
        siae_3 = SiaeFactory(kind=KIND_HANDICAP_LIST[0])

        for siae in [siae_1, siae_2, siae_3]:
            siae_activity = SiaeActivityFactory(
                siae=siae,
                sector=self.sector,
                with_zones_perimeter=True,
            )
            siae_activity.locations.set([self.perimeter_department])

        token = "a" * 64
        UserFactory(api_key=token)
        self.authenticated_client = self.client_class(headers={"authorization": f"Bearer {token}"})

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

    def test_negative_budget(self):
        """Test with a negative budget"""
        response = self.authenticated_client.get(self.url, {"sector": self.sector.slug, "budget": -1})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_siaes(self):
        """Test with no siaes"""
        other_sector = SectorFactory(group=self.sector.group)
        response = self.authenticated_client.get(self.url, {"sector": other_sector.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["potential_siaes"], 0)

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
        self.assertEqual(response.data["siaes_with_super_badge"], 1)

        # if there is no budget, there is no recommendation
        self.assertNotIn("recommendation", response.data)
        self.assertNotIn("ca_average", response.data)
        self.assertNotIn("eco_dependency", response.data)

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
        self.assertEqual(response.data["siaes_with_super_badge"], 1)

    def test_with_budget(self):
        """Test with a valid budget"""

        response = self.authenticated_client.get(self.url, {"sector": self.sector.slug, "budget": 100000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["potential_siaes"], 3)

        # siaes with ca: 200000 + 1000000 = 1200000 (2 siaes so avg = 600000)
        self.assertEqual(response.data["ca_average"], 600000)
        # 100000 / 600000 * 100 = 16.67 -> round to 17
        self.assertEqual(response.data["eco_dependency"], 17)
        self.assertEqual(response.data["recommendation"]["title"], "Clause sociale d'exécution")

    def test_recommendation_more_than_30_siaes(self):
        """
        Test with more than 30 siaes
        Create 31 siaes with CA values take times but it's necessary for the calculation of ca average and eco dep
        """
        # Specific sector with 31 siaes to avoid interference with existing SIAEs and avoid random failure
        specific_sector = SectorFactory(group=self.sector.group)
        # Create 31 SIAEs with CA values
        siaes = SiaeFactory.create_batch(31, ca=1000000)
        for siae in siaes:
            siae_activity_1 = SiaeActivityFactory(
                siae=siae,
                sector=specific_sector,
                with_zones_perimeter=True,
            )
            siae_activity_1.locations.set([self.perimeter_department])

        response = self.authenticated_client.get(self.url, {"sector": specific_sector.slug, "budget": 50000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["potential_siaes"], 31)
        self.assertEqual(response.data["ca_average"], 1000000)
        self.assertEqual(response.data["eco_dependency"], 5.0)  # 50000 / 1000000 * 100
        self.assertEqual(response.data["recommendation"]["title"], "Réservation totale")

        response = self.authenticated_client.get(self.url, {"sector": specific_sector.slug, "budget": 500000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["potential_siaes"], 31)
        self.assertEqual(response.data["ca_average"], 1000000)
        self.assertEqual(response.data["eco_dependency"], 50.0)  # 500000 / 1000000 * 100
        self.assertEqual(response.data["recommendation"]["title"], "Lot réservé")

    def test_recommendation_more_than_10_siaes(self):
        # Specific sector with 11 siaes
        specific_sector = SectorFactory(group=self.sector.group)
        # Create 11 SIAEs with CA values
        siaes = SiaeFactory.create_batch(11, ca=1000000)
        for siae in siaes:
            siae_activity_1 = SiaeActivityFactory(
                siae=siae,
                sector=specific_sector,
                with_zones_perimeter=True,
            )
            siae_activity_1.locations.set([self.perimeter_department])

        response = self.authenticated_client.get(self.url, {"sector": specific_sector.slug, "budget": 50000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["potential_siaes"], 11)
        self.assertEqual(response.data["recommendation"]["title"], "Lot réservé")

    def test_recommendation_no_siae(self):
        # Specific sector with 0 siaes
        specific_sector = SectorFactory(group=self.sector.group)

        response = self.authenticated_client.get(self.url, {"sector": specific_sector.slug, "budget": 50000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["potential_siaes"], 0)
        self.assertEqual(response.data["recommendation"]["title"], "Aucun potentiel inclusif identifié")
