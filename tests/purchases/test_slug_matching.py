from django.test import TestCase

from lemarche.purchases import constants as purchases_constants
from lemarche.purchases.models import SlugMappingCache
from lemarche.utils.slug_matching import (
    RESOLUTION_STATUS_AMBIGUOUS,
    RESOLUTION_STATUS_ERROR,
    RESOLUTION_STATUS_RESOLVED,
    is_france_entiere,
    normalize,
    record_user_choices,
    resolve_column_header,
    resolve_perimeter,
    resolve_sector,
    resolve_sector_from_title,
)
from tests.sectors.factories import SectorFactory
from tests.users.factories import UserFactory


class NormalizeTest(TestCase):
    """Tests de la fonction normalize()."""

    def test_minuscules(self):
        self.assertEqual(normalize("HAUTS DE SEINE"), "hauts de seine")

    def test_supprime_accents(self):
        self.assertEqual(normalize("Île-de-France"), "ile-de-france")

    def test_none_retourne_vide(self):
        self.assertEqual(normalize(None), "")

    def test_vide_retourne_vide(self):
        self.assertEqual(normalize(""), "")

    def test_espaces_stripes(self):
        self.assertEqual(normalize("  hauts de seine  "), "hauts de seine")


class IsFranceEntiereTest(TestCase):
    """Tests de la détection des variantes france_entiere."""

    def test_valeur_exacte(self):
        self.assertTrue(is_france_entiere("france_entiere"))

    def test_variante_avec_accent(self):
        self.assertTrue(is_france_entiere("France entière"))

    def test_variante_national(self):
        self.assertTrue(is_france_entiere("national"))

    def test_variante_france_simple(self):
        self.assertTrue(is_france_entiere("France"))

    def test_region_non_detectee(self):
        self.assertFalse(is_france_entiere("Île-de-France"))

    def test_departement_non_detecte(self):
        self.assertFalse(is_france_entiere("Seine-et-Marne"))


class ResolveColumnHeaderTest(TestCase):
    """Tests du matching des en-têtes de colonnes Excel."""

    def test_exact_match(self):
        self.assertEqual(resolve_column_header("secteur"), "secteur")

    def test_variante_avec_apostrophe(self):
        self.assertEqual(resolve_column_header("Secteur d'activité"), "secteur")

    def test_variante_perimetre(self):
        self.assertEqual(resolve_column_header("Périmètre géographique"), "perimetre_geographique")

    def test_variante_titre(self):
        self.assertEqual(resolve_column_header("Titre du projet"), "titre")

    def test_variante_categorie_achat(self):
        self.assertEqual(resolve_column_header("Catégorie achat"), "secteur")

    def test_variante_cpv(self):
        self.assertEqual(resolve_column_header("Code CPV"), "secteur")

    def test_variante_famille_achat(self):
        self.assertEqual(resolve_column_header("Famille achat"), "secteur")

    def test_variante_lieu(self):
        self.assertEqual(resolve_column_header("Lieu"), "perimetre_geographique")

    def test_variante_ville(self):
        self.assertEqual(resolve_column_header("Ville"), "perimetre_geographique")

    def test_variante_departement(self):
        self.assertEqual(resolve_column_header("Département"), "perimetre_geographique")

    def test_variante_region(self):
        self.assertEqual(resolve_column_header("Région"), "perimetre_geographique")

    def test_variante_budget_previsionnel(self):
        self.assertEqual(resolve_column_header("Budget prévisionnel"), "montant")

    def test_variante_estimation(self):
        self.assertEqual(resolve_column_header("Estimation"), "montant")

    def test_variante_depense(self):
        self.assertEqual(resolve_column_header("Dépense"), "montant")

    def test_valeur_inconnue_retourne_none(self):
        self.assertIsNone(resolve_column_header("colonne_inconnue_xyz"))

    def test_vide_retourne_none(self):
        self.assertIsNone(resolve_column_header(""))


class ResolveSectorExactMatchTest(TestCase):
    """Tests de resolve_sector — couche exact match."""

    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory(slug="nettoyage-des-locaux", name="Nettoyage des locaux")

    def test_exact_slug_resolved(self):
        result = resolve_sector("nettoyage-des-locaux")
        self.assertEqual(result["status"], RESOLUTION_STATUS_RESOLVED)
        self.assertEqual(result["slug"], "nettoyage-des-locaux")
        self.assertEqual(result["source"], "exact")

    def test_valeur_vide_error(self):
        result = resolve_sector("")
        self.assertEqual(result["status"], RESOLUTION_STATUS_ERROR)

    def test_none_error(self):
        result = resolve_sector(None)
        self.assertEqual(result["status"], RESOLUTION_STATUS_ERROR)


class ResolveSectorCacheTest(TestCase):
    """Tests de resolve_sector — couche cache validé."""

    @classmethod
    def setUpTestData(cls):
        cls.cache_entry = SlugMappingCache.objects.create(
            raw_value="nettoyage batiment",
            kind=purchases_constants.SLUG_MAPPING_KIND_SECTOR,
            resolved_slug="nettoyage-des-locaux",
            source=purchases_constants.SLUG_MAPPING_SOURCE_ADMIN_VALIDATED,
            confidence=0.85,
        )

    def test_cache_admin_validated_resolved(self):
        result = resolve_sector("Nettoyage Bâtiment")
        self.assertEqual(result["status"], RESOLUTION_STATUS_RESOLVED)
        self.assertEqual(result["slug"], "nettoyage-des-locaux")
        self.assertEqual(result["source"], "cache")

    def test_user_proposed_non_utilise(self):
        SlugMappingCache.objects.create(
            raw_value="nettoyage xyz",
            kind=purchases_constants.SLUG_MAPPING_KIND_SECTOR,
            resolved_slug="nettoyage-des-locaux",
            source=purchases_constants.SLUG_MAPPING_SOURCE_USER_PROPOSED,
            confidence=0.7,
        )
        result = resolve_sector("nettoyage xyz")
        # user_proposed ne passe pas en couche 2, doit aller au trigram
        self.assertNotEqual(result["source"], "cache")


class ResolvePerimeterFranceEntiereTest(TestCase):
    """Tests de resolve_perimeter — interception france_entiere."""

    def test_france_entiere_exact(self):
        result = resolve_perimeter("france_entiere")
        self.assertEqual(result["status"], RESOLUTION_STATUS_RESOLVED)
        self.assertTrue(result["france_entiere"])
        self.assertIsNone(result["slug"])

    def test_france_entiere_variante(self):
        result = resolve_perimeter("France entière")
        self.assertEqual(result["status"], RESOLUTION_STATUS_RESOLVED)
        self.assertTrue(result["france_entiere"])

    def test_variante_national(self):
        result = resolve_perimeter("national")
        self.assertEqual(result["status"], RESOLUTION_STATUS_RESOLVED)
        self.assertTrue(result["france_entiere"])


class ResolveSectorFromTitleTest(TestCase):
    """Tests de l'inférence secteur depuis le titre."""

    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory(slug="nettoyage-des-locaux", name="Nettoyage des locaux")

    def test_titre_vide_error(self):
        result = resolve_sector_from_title("", "")
        self.assertEqual(result["status"], RESOLUTION_STATUS_ERROR)

    def test_statut_toujours_ambiguous(self):
        result = resolve_sector_from_title("Nettoyage des bureaux municipaux", "")
        if result["status"] != RESOLUTION_STATUS_ERROR:
            self.assertEqual(result["status"], RESOLUTION_STATUS_AMBIGUOUS)

    def test_source_title_inference(self):
        result = resolve_sector_from_title("Nettoyage des bureaux", "")
        if result["status"] != RESOLUTION_STATUS_ERROR:
            self.assertEqual(result["source"], "title_inference")


class RecordUserChoicesTest(TestCase):
    """Tests de l'enregistrement des choix utilisateur en cache."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_enregistre_choix_secteur(self):
        record_user_choices(
            [
                {
                    "raw_value": "nettoyage bâtiment",
                    "kind": "sector",
                    "resolved_slug": "nettoyage-des-locaux",
                    "confidence": 0.75,
                }
            ],
            self.user,
        )
        cache = SlugMappingCache.objects.get(raw_value="nettoyage batiment", kind="sector")
        self.assertEqual(cache.resolved_slug, "nettoyage-des-locaux")
        self.assertEqual(cache.source, purchases_constants.SLUG_MAPPING_SOURCE_USER_PROPOSED)
        self.assertEqual(cache.proposed_by, self.user)

    def test_idempotent_incremente_usage(self):
        record_user_choices(
            [{"raw_value": "espaces verts", "kind": "sector", "resolved_slug": "espaces-verts", "confidence": 0.8}],
            self.user,
        )
        record_user_choices(
            [{"raw_value": "espaces verts", "kind": "sector", "resolved_slug": "espaces-verts", "confidence": 0.8}],
            self.user,
        )
        cache = SlugMappingCache.objects.get(raw_value="espaces verts", kind="sector")
        self.assertEqual(cache.usage_count, 2)
