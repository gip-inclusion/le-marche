import datetime
import json
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from lemarche.siaes.factories import SiaeFactory
from lemarche.utils.apis.api_entreprise import siae_update_entreprise, siae_update_etablissement, siae_update_exercice


MOCK_ENTREPRISE_API_DATA = """
{
    "data": {
        "siren": "130025265",
        "rna": "W751004076",
        "siret_siege_social": "13002526500013",
        "type": "personne_morale",
        "personne_morale_attributs": {
            "raison_sociale": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
            "sigle": "DINUM"
        },
        "personne_physique_attributs": {
            "pseudonyme": "DJ Falcon",
            "prenom_usuel": "Jean",
            "prenom_1": "Jean",
            "prenom_2": "Jacques",
            "prenom_3": "Pierre",
            "prenom_4": "Paul",
            "nom_usage": "Dupont",
            "nom_naissance": "Martin",
            "sexe": "M"
        },
        "categorie_entreprise": "GE",
        "status_diffusion": "diffusible",
        "diffusable_commercialement": true,
        "forme_juridique": {
            "code": "7120",
            "libelle": "Service central d'un ministère"
        },
        "activite_principale": {
            "code": "8411Z",
            "libelle": "Administration publique générale",
            "nomenclature": "NAFRev2"
        },
        "tranche_effectif_salarie": {
            "code": "51",
            "intitule": "2 000 à 4 999 salariés",
            "date_reference": "2016",
            "de": 2000,
            "a": 4999
        },
        "etat_administratif": "A",
        "economie_sociale_et_solidaire": true,
        "date_creation": 1634103818,
        "date_cessation": 1634133818
    },
    "links": {
        "siege_social": "https://entreprises.api.gouv.fr/api/v3/insee/etablissements/30613890001294",
        "siege_social_adresse": "https://entreprises.api.gouv.fr/api/v3/insee/etablissements/30613890001294/adresse"
    },
    "meta": {
        "date_derniere_mise_a_jour": 1618396818,
        "redirect_from_siren": "306138900"
    }
}
"""


class TestSiaeUpdateEntreprise(TestCase):
    def setUp(self):
        self.siae = SiaeFactory(siret="13002526500013")

    @patch("requests.get")
    def test_siae_update_entreprise(self, mock_api):
        mock_response = mock_api.return_value
        mock_response.json.return_value = json.loads(MOCK_ENTREPRISE_API_DATA)
        mock_response.status_code = 200

        result, entreprise = siae_update_entreprise(self.siae)

        self.siae.refresh_from_db()

        # Assert the result
        self.assertEqual(result, 1)
        self.assertIsNotNone(entreprise)

        # Assert the updates
        self.assertEqual(self.siae.api_entreprise_forme_juridique, "Service central d'un ministère")
        self.assertEqual(self.siae.api_entreprise_forme_juridique_code, "7120")
        self.assertLess((timezone.now() - self.siae.api_entreprise_entreprise_last_sync_date).total_seconds(), 60)


MOCK_ETABLISSEMENT_API_DATA = """
{
    "data": {
        "siret": "30613890001294",
        "siege_social": true,
        "etat_administratif": "A",
        "date_fermeture": 1634133818,
        "status_diffusion": "diffusible",
        "activite_principale": {
            "code": "8411Z",
            "libelle": "Administration publique générale",
            "nomenclature": "NAFRev2"
        },
        "tranche_effectif_salarie": {
            "code": "51",
            "intitule": "2 000 à 4 999 salariés",
            "date_reference": "2016",
            "de": 2000,
            "a": 4999
        },
        "diffusable_commercialement": true,
        "enseigne": "Coiff Land, CoiffureLand",
        "unite_legale": {
            "siren": "130025265",
            "rna": null,
            "siret_siege_social": "13002526500013",
            "type": "personne_morale",
            "status_diffusion": "diffusible",
            "personne_morale_attributs": {
                "raison_sociale": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
                "sigle": "DINUM"
            },
            "personne_physique_attributs": {
                "pseudonyme": "DJ Falcon",
                "prenom_usuel": "Jean",
                "prenom_1": "Jean",
                "prenom_2": "Jacques",
                "prenom_3": "Pierre",
                "prenom_4": "Paul",
                "nom_usage": "Dupont",
                "nom_naissance": "Dubois",
                "sexe": "M"
            },
            "categorie_entreprise": "GE",
            "diffusable_commercialement": true,
            "forme_juridique": {
                "code": "7120",
                "libelle": "Service central d'un ministère"
            },
            "activite_principale": {
                "code": "8411Z",
                "libelle": "Administration publique générale",
                "nomenclature": "NAFRev2"
            },
            "tranche_effectif_salarie": {
                "code": "51",
                "intitule": "2 000 à 4 999 salariés",
                "date_reference": "2016",
                "de": 2000,
                "a": 4999
            },
            "etat_administratif": "A",
            "economie_sociale_et_solidaire": true,
            "date_creation": 1634103818
        },
        "adresse": {
            "numero_voie": "22",
            "indice_repetition_voie": null,
            "type_voie": "RUE",
            "libelle_voie": "DE LA PAIX",
            "complement_adresse": "ZAE SAINT GUENAULT",
            "code_commune": "75112",
            "code_postal": "75016",
            "distribution_speciale": "dummy",
            "code_cedex": "75590",
            "libelle_cedex": "PARIS CEDEX 12",
            "libelle_commune": "PARIS 12",
            "libelle_commune_etranger": "dummy",
            "code_pays_etranger": "99132",
            "libelle_pays_etranger": "ROYAUME-UNI",
            "status_diffusion": "diffusible",
            "acheminement_postal": {
                "l1": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
                "l2": "JEAN MARIE DURAND",
                "l3": "ZAE SAINT GUENAULT",
                "l4": "51 BIS RUE DE LA PAIX",
                "l5": "CS 72809",
                "l6": "75256 PARIX CEDEX 12",
                "l7": "FRANCE"
            }
        },
        "date_creation": 1634103818
    },
    "links": {
        "unite_legale": "https://entreprise.api.gouv.fr/api/v3/insee/unites_legales/130025265"
    },
    "meta": {
        "date_derniere_mise_a_jour": 1618396818,
        "redirect_from_siret": "30613890000010"
    }
}
"""


class TestSiaeUpdateEtablissement(TestCase):
    def setUp(self):
        self.siae = SiaeFactory(siret="30613890001294")

    @patch("requests.get")
    def test_siae_update_etablissement(self, mock_api):
        mock_response = mock_api.return_value
        mock_response.json.return_value = json.loads(MOCK_ETABLISSEMENT_API_DATA)
        mock_response.status_code = 200

        result, etablissement = siae_update_etablissement(self.siae)

        # Assert the result
        self.assertEqual(result, 1)
        self.assertIsNotNone(etablissement)

        # Assert the updates
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.siret, "30613890001294")
        self.assertEqual(self.siae.api_entreprise_employees, "2 000 à 4 999 salariés")
        self.assertEqual(self.siae.api_entreprise_employees_year_reference, "2016")
        self.assertEqual(self.siae.api_entreprise_date_constitution, datetime.date(2021, 10, 13))
        self.assertLess((timezone.now() - self.siae.api_entreprise_etablissement_last_sync_date).total_seconds(), 60)


MOCK_EXERCICES_API_DATA = """
{
    "data": [
        {
            "data": {
                "chiffre_affaires": 900001,
                "date_fin_exercice": "2015-12-01"
            },
            "links": {},
            "meta": {}
        }
    ],
    "meta": {},
    "links": {}
}
"""


class TestSiaeUpdateExercice(TestCase):
    def setUp(self):
        self.siae = SiaeFactory(siret="30613890001294")

    @patch("requests.get")
    def test_siae_update_exercice(self, mock_api):
        mock_response = mock_api.return_value
        mock_response.json.return_value = json.loads(MOCK_EXERCICES_API_DATA)
        mock_response.status_code = 200

        siae_update_exercice(self.siae)

        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_ca, 900001)
        self.assertEqual(self.siae.api_entreprise_ca_date_fin_exercice, datetime.date(2015, 12, 1))
        self.assertLess((timezone.now() - self.siae.api_entreprise_exercice_last_sync_date).total_seconds(), 60)
