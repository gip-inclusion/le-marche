from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from lemarche.perimeters.models import Perimeter
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from tests.perimeters.factories import PerimeterFactory
from tests.sectors.factories import SectorFactory
from tests.siaes.factories import SiaeActivityFactory, SiaeFactory
from tests.users.factories import UserFactory


class InclusivePotentialViewTests(TestCase):
    def setUp(self):
        self.url = reverse("api:inclusive-potential")

        self.sector = SectorFactory()
        self.perimeter_department = PerimeterFactory(
            name="Paris", kind=Perimeter.KIND_DEPARTMENT, insee_code="75", region_code="11"
        )

        siae_1 = SiaeFactory(kind=KIND_INSERTION_LIST[0], api_entreprise_ca=200000, c2_etp_count=10)
        siae_2 = SiaeFactory(
            department="75",
            kind=KIND_INSERTION_LIST[1],
            super_badge=True,
            ca=1000000,
            api_entreprise_ca=500000,
            c2_etp_count=20,
            employees_insertion_count=15,  # will be ignored by the calculation because use c2_etp_count instead
            employees_permanent_count=9,
            has_won_contract_last_3_years=True,
        )
        siae_3 = SiaeFactory(kind=KIND_HANDICAP_LIST[0], employees_insertion_count=10, employees_permanent_count=7)

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
        self.assertEqual(response.data["local_siaes"], 1)
        self.assertEqual(response.data["siaes_with_super_badge"], 1)
        self.assertEqual(response.data["siaes_with_won_contract"], 1)
        self.assertEqual(response.data["employees_insertion_average"], 13.33)
        self.assertEqual(response.data["employees_permanent_average"], 5.33)

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

    def test_with_city_perimeter(self):
        """Test with a city (commune) perimeter — should return structures able to intervene in that city"""
        # Create a city in department 75 — existing siaes have activities located in department 75
        perimeter_city = PerimeterFactory(
            name="Paris 1er",
            kind=Perimeter.KIND_CITY,
            insee_code="75001",
            department_code="75",
            region_code="11",
            coords=Point(2.3488, 48.8534),
        )

        response = self.authenticated_client.get(
            self.url, {"sector": self.sector.slug, "perimeter": perimeter_city.slug}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["perimeter_kind"], Perimeter.KIND_CITY)
        # All 3 siaes have activities in department 75, which covers the city
        self.assertEqual(response.data["potential_siaes"], 3)
        self.assertFalse(response.data["france_entiere"])

    def test_france_entiere(self):
        """Test france_entiere=true — only structures with national intervention capacity"""
        specific_sector = SectorFactory(group=self.sector.group)

        # 2 SIAEs with national coverage
        siaes_country = SiaeFactory.create_batch(2)
        for siae in siaes_country:
            SiaeActivityFactory(siae=siae, sector=specific_sector, with_country_perimeter=True)

        # 1 SIAE with zone-based coverage only
        siae_zones = SiaeFactory()
        activity_zones = SiaeActivityFactory(siae=siae_zones, sector=specific_sector, with_zones_perimeter=True)
        activity_zones.locations.set([self.perimeter_department])

        response = self.authenticated_client.get(
            self.url, {"sector": specific_sector.slug, "france_entiere": "true"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["france_entiere"])
        self.assertIsNone(response.data["perimeter_name"])
        # Only the 2 national coverage SIAEs should be returned
        self.assertEqual(response.data["potential_siaes"], 2)

    def test_all_france(self):
        """Test without perimeter — returns all structures in France regardless of their coverage zone"""
        specific_sector = SectorFactory(group=self.sector.group)

        siae_country = SiaeFactory()
        SiaeActivityFactory(siae=siae_country, sector=specific_sector, with_country_perimeter=True)

        siae_zones = SiaeFactory()
        activity_zones = SiaeActivityFactory(siae=siae_zones, sector=specific_sector, with_zones_perimeter=True)
        activity_zones.locations.set([self.perimeter_department])

        response = self.authenticated_client.get(self.url, {"sector": specific_sector.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["france_entiere"])
        self.assertIsNone(response.data["perimeter_name"])
        # Both structures should be returned regardless of their coverage
        self.assertEqual(response.data["potential_siaes"], 2)

    def test_france_entiere_and_perimeter_mutually_exclusive(self):
        """Test that france_entiere and perimeter cannot be used together"""
        response = self.authenticated_client.get(
            self.url,
            {"sector": self.sector.slug, "france_entiere": "true", "perimeter": self.perimeter_department.slug},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
