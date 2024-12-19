# https://github.com/betagouv/itou/blob/master/itou/utils/apis/api_entreprise.py

import logging
from dataclasses import dataclass
from datetime import date, datetime

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.http import urlencode

from lemarche.siaes.models import Siae


logger = logging.getLogger(__name__)

API_ENTREPRISE_REASON = "Mise à jour données Marché de la plateforme de l'Inclusion"
DATE_FORMAT = "%Y-%m-%d"


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


def entreprise_get_or_error(siren, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprise.api.gouv.fr
    documentation: https://entreprise.api.gouv.fr/developpeurs/openapi#tag/Informations-generales/paths/~1v3~1insee~1sirene~1unites_legales~1%7Bsiren%7D/get  # noqa

    Format info:
    - "date_derniere_mise_a_jour": 1449183600
    """
    error = None

    query_string = urlencode(
        {
            "recipient": settings.API_ENTREPRISE_RECIPIENT,
            "context": settings.API_ENTREPRISE_CONTEXT,
            "object": reason,
        }
    )
    url = f"{settings.API_ENTREPRISE_BASE_URL}/insee/sirene/unites_legales/{siren}?{query_string}"
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


def siae_update_entreprise(siae):
    if siae.siret:
        siae_siren = siae.siret[:9]
        entreprise, error = entreprise_get_or_error(siae_siren, reason=API_ENTREPRISE_REASON)
        if error:
            return 0, error

        update_data = dict()
        if entreprise:
            if entreprise.forme_juridique:
                update_data["api_entreprise_forme_juridique"] = entreprise.forme_juridique
            if entreprise.forme_juridique_code:
                update_data["api_entreprise_forme_juridique_code"] = entreprise.forme_juridique_code

        update_data["api_entreprise_entreprise_last_sync_date"] = timezone.now()
        Siae.objects.filter(id=siae.id).update(**update_data)

        return 1, entreprise
    return 0, f"SIAE {siae.id} without SIREN"


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

    query_string = urlencode(
        {
            "recipient": settings.API_ENTREPRISE_RECIPIENT,
            "context": settings.API_ENTREPRISE_CONTEXT,
            "object": reason,
        }
    )
    url = f"{settings.API_ENTREPRISE_BASE_URL}/insee/sirene/etablissements/{siret}?{query_string}"
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


def siae_update_etablissement(siae):
    if siae.siret:
        etablissement, error = etablissement_get_or_error(siae.siret, reason=API_ENTREPRISE_REASON)
        if error:
            return 0, error

        update_data = dict()
        if etablissement:
            if etablissement.employees:
                update_data["api_entreprise_employees"] = (
                    etablissement.employees
                    if (etablissement.employees != "Unités non employeuses")
                    else "Non renseigné"
                )
            if etablissement.employees_date_reference:
                update_data["api_entreprise_employees_year_reference"] = etablissement.employees_date_reference
            if etablissement.date_constitution:
                update_data["api_entreprise_date_constitution"] = etablissement.date_constitution

        update_data["api_entreprise_etablissement_last_sync_date"] = timezone.now()
        Siae.objects.filter(id=siae.id).update(**update_data)

        return 1, etablissement

    return 0, f"SIAE {siae.id} without SIRET"


def exercice_get_or_error(siret, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprises.api.gouv.fr
    documentation: https://entreprise.api.gouv.fr/developpeurs/openapi#tag/Informations-financieres/paths/~1v3~1dgfip~1etablissements~1%7Bsiret%7D~1chiffres_affaires/get  # noqa

    Format info:
    - "date_fin_exercice": "2024-12-17"

    Often returns errors: 404, 422, 502
    """
    error = None

    query_string = urlencode(
        {
            "recipient": settings.API_ENTREPRISE_RECIPIENT,
            "context": settings.API_ENTREPRISE_CONTEXT,
            "object": reason,
        }
    )
    url = f"{settings.API_ENTREPRISE_BASE_URL}/dgfip/etablissements/{siret}/chiffres_affaires?{query_string}"
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


def siae_update_exercice(siae):
    if siae.siret:
        exercice, error = exercice_get_or_error(siae.siret, reason=API_ENTREPRISE_REASON)
        if error:
            return 0, error

        update_data = dict()

        if exercice:
            update_data = dict()
            if exercice.chiffre_affaires:
                update_data["api_entreprise_ca"] = exercice.chiffre_affaires
            if exercice.date_fin_exercice:
                update_data["api_entreprise_ca_date_fin_exercice"] = datetime.strptime(
                    exercice.date_fin_exercice, DATE_FORMAT
                ).date()

        update_data["api_entreprise_exercice_last_sync_date"] = timezone.now()
        Siae.objects.filter(id=siae.id).update(**update_data)

        return 1, exercice
    return 0, f"SIAE {siae.id} without SIRET"
