# https://github.com/betagouv/itou/blob/master/itou/utils/apis/api_entreprise.py

import logging
from dataclasses import dataclass
from datetime import date

import requests
from django.conf import settings
from django.utils.http import urlencode


logger = logging.getLogger(__name__)

API_ENTREPRISE_REASON = "Mise à jour données Marché de la plateforme de l'Inclusion"


@dataclass
class Entreprise:
    forme_juridique: str
    forme_juridique_code: str


@dataclass
class Etablissement:
    naf: str
    is_closed: bool
    is_head_office: bool
    employees: str
    employees_date_reference: str
    date_constitution: date


@dataclass
class Exercice:
    chiffre_affaires: str
    date_fin_exercice: date


def get_url_endpoint(endpoint: str, reason: str) -> str:
    query_string = urlencode(
        {
            "recipient": settings.API_ENTREPRISE_RECIPIENT,
            "context": settings.API_ENTREPRISE_CONTEXT,
            "object": reason,
        }
    )
    return f"{settings.API_ENTREPRISE_BASE_URL}/{endpoint}?{query_string}"


def entreprise_get_or_error(siren, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprise.api.gouv.fr
    documentation: https://entreprise.api.gouv.fr/developpeurs/openapi#tag/Informations-generales/paths/~1v3~1insee~1sirene~1unites_legales~1%7Bsiren%7D/get  # noqa

    Format info:
    - "date_derniere_mise_a_jour": 1449183600
    """
    error = None

    url = get_url_endpoint(f"insee/sirene/unites_legales/{siren}", reason)
    headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        response = r.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code

        match status_code:
            case 422:
                error = f"SIREN « {siren} » non reconnu."
            case 404:
                error = f"SIREN « {siren} » 404 ?"
            case _:
                logger.error("Error while fetching `%s`: %s", url, e)
                error = "Problème de connexion à la base Sirene. Essayez ultérieurement."
        return None, error
    except requests.ReadTimeout as e:  # noqa
        logger.error("Error while fetching `%s`: %s", url, e)
        error = "The read operation timed out"
        return None, error

    if response and response.get("errors"):
        error = response["errors"][0]
        return None, error

    data = response["data"]
    if not data.get("forme_juridique"):
        logger.error(f"Invalid format of response from API Entreprise - Entreprise (siren={siren}): {response}")
        error = "Le format de la réponse API Entreprise est non valide."
        return None, error

    entreprise = Entreprise(
        forme_juridique=data["forme_juridique"]["libelle"],
        forme_juridique_code=data["forme_juridique"]["code"],
    )
    return entreprise, None


def etablissement_get_or_error(siret, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprise.api.gouv.fr
    documentation: https://entreprise.api.gouv.fr/developpeurs/openapi#tag/Informations-generales/paths/~1v3~1insee~1sirene~1etablissements~1%7Bsiret%7D/get  # noqa

    Format info:
    - "date_mise_a_jour": 1449183600
    - "date_reference": "2014"
    - "date_creation": 1108594800
    - "date_fermeture": 1315173600
    """
    error = None

    url = get_url_endpoint(f"insee/sirene/etablissements/{siret}", reason)
    headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        response = r.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        match status_code:
            case 422:
                error = f"SIRET « {siret} » non reconnu."  # TODO: check v3 error code
            case 404:
                error = f"SIRET « {siret} » 404 ?"
            case _:
                # logger.error("Error while fetching `%s`: %s", url, e)
                error = f"Problème de connexion à la base Sirene. Essayez ultérieurement. ({status_code})"
        return None, error
    except requests.ReadTimeout as e:  # noqa
        logger.error("Error while fetching `%s`: %s", url, e)
        error = "The read operation timed out"
        return None, error

    if response and response.get("errors"):
        error = response["errors"][0]
        return None, error

    data = response["data"]
    if (
        not data.get("activite_principale")
        or not data.get("etat_administratif")
        or not data.get("tranche_effectif_salarie")
        or not data.get("date_creation")
    ):
        logger.error(f"Invalid format of response from API Entreprise - Etablissement (siret={siret}): {response}")
        error = "Le format de la réponse API Entreprise est non valide."
        return None, error

    etablissement = Etablissement(
        naf=data["activite_principale"]["code"],
        is_closed=data["etat_administratif"] == "F",
        is_head_office=data.get("siege_social", False),
        employees=data["tranche_effectif_salarie"]["intitule"],
        employees_date_reference=data["tranche_effectif_salarie"]["date_reference"],
        date_constitution=date.fromtimestamp(data["date_creation"]),
    )
    return etablissement, None


def exercice_get_or_error(siret, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprises.api.gouv.fr
    documentation: https://entreprise.api.gouv.fr/developpeurs/openapi#tag/Informations-financieres/paths/~1v3~1dgfip~1etablissements~1%7Bsiret%7D~1chiffres_affaires/get  # noqa

    Format info:
    - "date_fin_exercice": "2024-12-17"

    Often returns errors: 404, 422, 502
    """
    error = None

    url = get_url_endpoint(f"dgfip/etablissements/{siret}/chiffres_affaires", reason)
    headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        response = r.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code

        if status_code == 422:
            error = f"SIRET {siret} non reconnu."
        else:
            logger.error("Error while fetching `%s`: %s", url, e)
            error = f"Problème de connexion à la base Sirene. Essayez ultérieurement. ({status_code})"
        return None, error
    except requests.ReadTimeout as e:  # noqa
        logger.error("Error while fetching `%s`: %s", url, e)
        error = "The read operation timed out"
        return None, error

    if response and response.get("errors"):
        error = response["errors"][0]
        return None, error

    if not response.get("data") or not len(response["data"]):
        logger.error(f"Invalid format of response from API Entreprise - Exercice (siret={siret}): {response}")
        error = "Le format de la réponse API Entreprise est non valide."
        return None, error

    exercice = Exercice(
        chiffre_affaires=response["data"][0]["data"]["chiffre_affaires"],
        date_fin_exercice=response["data"][0]["data"]["date_fin_exercice"],
    )
    return exercice, None
