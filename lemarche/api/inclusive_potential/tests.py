from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.users.factories import UserFactory


class InclusivePotentialViewTests(TestCase):
    def setUp(self):
        self.url = reverse("api:inclusive-potential")

        self.sector = SectorFactory()
        self.perimeter_department = PerimeterFactory(
            name="Paris", kind=Perimeter.KIND_DEPARTMENT, insee_code="75", region_code="11"
        )

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

    @patch("lemarche.api.inclusive_potential.views.Siae.objects.filter_with_potential_through_activities")
    def test_with_sector_and_perimeter(self, mock_filter):
        """Test with valid sector and perimeter"""
        # Simulate the query result
        mock_queryset = Mock()
        mock_queryset.count.return_value = 10
        mock_filter.return_value = mock_queryset

        response = self.authenticated_client.get(
            self.url, {"sector": self.sector.slug, "perimeter": self.perimeter_department.slug}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sector_name"], self.sector.name)
        self.assertEqual(response.data["perimeter_name"], self.perimeter_department.name)
        self.assertEqual(response.data["perimeter_kind"], self.perimeter_department.kind)
        self.assertEqual(response.data["potential_siaes"], 10)

    @patch("lemarche.api.inclusive_potential.views.Siae.objects.filter_with_potential_through_activities")
    def test_with_sector_only(self, mock_filter):
        """Test with only a valid sector (without perimeter)"""
        # Simulate the query result
        mock_queryset = Mock()
        mock_queryset.count.return_value = 25
        mock_filter.return_value = mock_queryset

        response = self.authenticated_client.get(self.url, {"sector": self.sector.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sector_name"], self.sector.name)
        self.assertEqual(response.data["perimeter_name"], None)
        self.assertEqual(response.data["perimeter_kind"], None)
        self.assertEqual(response.data["potential_siaes"], 25)
