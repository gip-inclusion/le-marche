from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.users.factories import UserFactory


class InclusivePotentialViewTests(TestCase):
    fixtures = [
        "lemarche/fixtures/django/0b_sectorgroups.json",
        "lemarche/fixtures/django/0c_sectors.json",
    ]

    def setUp(self):
        self.url = reverse("api:inclusive-potential")

        # Run the import_departements command
        call_command("import_departements")

        self.sector = Sector.objects.first()
        self.perimeter = Perimeter.objects.filter(kind="DEPARTMENT").first()

        self.token = "a" * 64
        UserFactory(api_key=self.token)
        self.authenticated_client = self.client_class(headers={"authorization": f"Bearer {self.token}"})

    def test_invalid_sector(self):
        """Test avec un secteur invalide"""
        response = self.authenticated_client.get(self.url, {"sector": "secteur-invalide"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_perimeter(self):
        """Test avec un périmètre invalide"""
        response = self.authenticated_client.get(
            self.url, {"sector": self.sector.slug, "perimeter": "perimetre-invalide"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("lemarche.api.inclusive_potential.views.Siae.objects.filter_with_potential_through_activities")
    @patch("lemarche.api.inclusive_potential.views.get_score_inclusif")
    def test_with_sector_and_perimeter(self, mock_get_score, mock_filter):
        """Test avec un secteur et un périmètre valides"""
        # Simulate the query result
        mock_queryset = Mock()
        mock_queryset.count.return_value = 10
        mock_filter.return_value = mock_queryset

        # Simulate the inclusive score
        mock_score = Mock()
        mock_score.score_inclusif = 3
        mock_score.inclusif_interpretation = "Bon potentiel"
        mock_get_score.return_value = mock_score

        response = self.authenticated_client.get(
            self.url, {"sector": self.sector.slug, "perimeter": self.perimeter.slug}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sector_name"], self.sector.name)
        self.assertEqual(response.data["perimeter_name"], self.perimeter.name)
        self.assertEqual(response.data["perimeter_kind"], self.perimeter.kind)
        self.assertEqual(response.data["potential_siaes"], 10)
        self.assertEqual(response.data["score_inclusif"], 3)
        self.assertEqual(response.data["inclusif_interpretation"], "Bon potentiel")

    @patch("lemarche.api.inclusive_potential.views.Siae.objects.filter_with_potential_through_activities")
    @patch("lemarche.api.inclusive_potential.views.get_score_inclusif")
    def test_with_sector_only(self, mock_get_score, mock_filter):
        """Test avec seulement un secteur valide (sans périmètre)"""
        # Simulate the query result
        mock_queryset = Mock()
        mock_queryset.count.return_value = 25
        mock_filter.return_value = mock_queryset

        # Simulate the inclusive score
        mock_score = Mock()
        mock_score.score_inclusif = 4
        mock_score.inclusif_interpretation = "Très bon potentiel"
        mock_get_score.return_value = mock_score

        response = self.authenticated_client.get(self.url, {"sector": self.sector.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sector_name"], self.sector.name)
        self.assertEqual(response.data["perimeter_name"], None)
        self.assertEqual(response.data["perimeter_kind"], None)
        self.assertEqual(response.data["potential_siaes"], 25)
        self.assertEqual(response.data["score_inclusif"], 4)
        self.assertEqual(response.data["inclusif_interpretation"], "Très bon potentiel")
