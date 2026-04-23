from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse

from lemarche.api.inclusive_potential.utils import PotentialData
from lemarche.users.models import User
from tests.perimeters.factories import PerimeterFactory
from tests.sectors.factories import SectorFactory
from tests.users.factories import UserFactory


ANALYSIS_URL = "dashboard:inclusive_potential_analysis"
TEMPLATE_URL = "dashboard:inclusive_potential_analysis_template"

MOCK_POTENTIAL_DATA = PotentialData(
    potential_siaes=15,
    insertion_siaes=10,
    handicap_siaes=5,
    local_siaes=8,
    siaes_with_super_badge=2,
    employees_insertion_average=12.5,
    employees_permanent_average=8.0,
)
MOCK_ANALYSIS_DATA = {
    "ca_average": 300000,
    "eco_dependency": 27,
    "recommendation": {
        "title": "Réservation totale",
        "response": "Vous pouvez réserver l'ensemble de votre projet d'achat à des fournisseurs inclusifs !",
        "explanation": None,
    },
}


class InclusivePotentialAnalysisViewAccessTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse(ANALYSIS_URL)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_buyer_can_access(self):
        self.client.force_login(self.user_buyer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analyser le potentiel inclusif")

    def test_authenticated_siae_user_can_access(self):
        self.client.force_login(self.user_siae)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_renders_empty_formset(self):
        self.client.force_login(self.user_buyer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)
        self.assertIn("sectors", response.context)
        self.assertIsNone(response.context["results"])


class InclusivePotentialAnalysisManualFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse(ANALYSIS_URL)
        cls.user = UserFactory(kind=User.KIND_BUYER)
        cls.sector = SectorFactory()
        cls.perimeter = PerimeterFactory(name="Paris", slug="paris")

    def _post_manual(self, data):
        self.client.force_login(self.user)
        return self.client.post(self.url, data)

    def _valid_formset_data(
        self, titre="Nettoyage de locaux", montant=80000, sector_slug=None, perimeter_slug="paris"
    ):
        sector_slug = sector_slug or self.sector.slug
        return {
            "mode": "manual",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-titre": titre,
            "form-0-description": "Description du projet",
            "form-0-secteur": sector_slug,
            "form-0-montant": str(montant),
            "form-0-perimeter_slug": perimeter_slug,
            "form-0-france_entiere": "",
        }

    @patch("lemarche.www.dashboard.views.get_inclusive_potential_data")
    def test_valid_form_returns_results(self, mock_analysis):
        mock_analysis.return_value = (MOCK_POTENTIAL_DATA, MOCK_ANALYSIS_DATA)
        response = self._post_manual(self._valid_formset_data())
        self.assertEqual(response.status_code, 200)
        results = response.context["results"]
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["error"])
        self.assertEqual(results[0]["potential_siaes"], 15)
        self.assertEqual(results[0]["recommendation_title"], "Réservation totale")

    @patch("lemarche.www.dashboard.views.get_inclusive_potential_data")
    def test_valid_form_without_montant_returns_results_without_recommendation(self, mock_analysis):
        mock_analysis.return_value = (MOCK_POTENTIAL_DATA, {})
        data = self._valid_formset_data(montant="")
        data["form-0-montant"] = ""
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        results = response.context["results"]
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["recommendation_title"])

    @patch("lemarche.www.dashboard.views.get_inclusive_potential_data")
    def test_multiple_projects_return_multiple_results(self, mock_analysis):
        mock_analysis.return_value = (MOCK_POTENTIAL_DATA, MOCK_ANALYSIS_DATA)
        sector2 = SectorFactory()
        data = {
            "mode": "manual",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-titre": "Projet nettoyage",
            "form-0-secteur": self.sector.slug,
            "form-0-montant": "80000",
            "form-0-perimeter_slug": "paris",
            "form-0-france_entiere": "",
            "form-1-titre": "Projet espaces verts",
            "form-1-secteur": sector2.slug,
            "form-1-montant": "45000",
            "form-1-perimeter_slug": "paris",
            "form-1-france_entiere": "",
        }
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        results = response.context["results"]
        self.assertEqual(len(results), 2)

    def test_missing_titre_shows_error(self):
        data = self._valid_formset_data(titre="")
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["results"])
        formset = response.context["formset"]
        self.assertTrue(formset.errors[0].get("titre") or formset.non_form_errors())

    def test_missing_secteur_shows_error(self):
        data = self._valid_formset_data()
        data["form-0-secteur"] = ""
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["results"])

    def test_missing_perimeter_and_no_france_entiere_shows_error(self):
        data = self._valid_formset_data(perimeter_slug="")
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["results"])

    @patch("lemarche.www.dashboard.views.get_inclusive_potential_data")
    def test_france_entiere_passes_none_perimeter(self, mock_analysis):
        mock_analysis.return_value = (MOCK_POTENTIAL_DATA, {})
        data = {
            "mode": "manual",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-titre": "Projet national",
            "form-0-secteur": self.sector.slug,
            "form-0-montant": "",
            "form-0-perimeter_slug": "",
            "form-0-france_entiere": "on",
        }
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        results = response.context["results"]
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        # Verify analysis was called with perimeter=None
        call_args = mock_analysis.call_args
        self.assertIsNone(call_args[0][1])  # perimeter arg is None

    def test_invalid_perimeter_slug_returns_error_result(self):
        data = self._valid_formset_data(perimeter_slug="slug-inexistant")
        response = self._post_manual(data)
        self.assertEqual(response.status_code, 200)
        # Either form-level error or result-level error
        formset_has_error = any(f.errors for f in response.context["formset"].forms)
        result_has_error = (
            response.context["results"] is not None
            and any(r.get("error") for r in response.context["results"])
        )
        self.assertTrue(formset_has_error or result_has_error)


class InclusivePotentialExcelTemplateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse(TEMPLATE_URL)
        cls.user = UserFactory(kind=User.KIND_BUYER)

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_downloads_xlsx(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("modele_analyse_potentiel_inclusif.xlsx", response["Content-Disposition"])

    def test_downloaded_file_has_correct_columns(self):
        import io
        import openpyxl

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        self.assertIn("titre", headers)
        self.assertIn("secteur", headers)
        self.assertIn("montant", headers)
        self.assertIn("perimetre_geographique", headers)
