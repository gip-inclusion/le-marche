# https://github.com/betagouv/itou/blob/master/itou/utils/apis/api_entreprise.py

import logging
from datetime import date, datetime

import httpx
from django.conf import settings
from django.utils import timezone
from django.utils.http import urlencode

from lemarche.siaes.models import Siae


logger = logging.getLogger(__name__)


API_ENTREPRISE_REASON = "Mise à jour donnéés Marché de la plateforme de l'Inclusion"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed


def etablissement_get_or_error(siret, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprises.api.gouv.fr
    documentation: https://doc.entreprise.api.gouv.fr/?json#etablissements-v2

    Format info:
    - "date_mise_a_jour": 1449183600
    - "date_reference": "2014"
    - "date_creation_etablissement": 1108594800
    - "date_fermeture": 1315173600
    """
    data = None
    etablissement = None
    error = None

    query_string = urlencode(
        {
            "recipient": settings.API_ENTREPRISE_RECIPIENT,
            "context": settings.API_ENTREPRISE_CONTEXT,
            "object": reason,
        }
    )

    url = f"{settings.API_ENTREPRISE_BASE_URL}/etablissements/{siret}?{query_string}"
    headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}

    try:
        r = httpx.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            error = f"SIRET « {siret} » non reconnu."
        elif e.response.status_code == 404:
            error = f"SIRET « {siret} » 404 ?"
        else:
            # logger.error("Error while fetching `%s`: %s", url, e)
            error = "Problème de connexion à la base Sirene. Essayez ultérieurement."
        return None, error
    except httpx.ReadTimeout as e:  # noqa
        # logger.error("Error while fetching `%s`: %s", url, e)
        error = "The read operation timed out"
        return None, error

    if data and data.get("errors"):
        error = data["errors"][0]
        return None, error

    if not data.get("etablissement") or not data["etablissement"].get("adresse"):
        # logger.error("Invalid format of response from API Entreprise")
        error = "Le format de la réponse API Entreprise est non valide."
        return None, error

    # address = data["etablissement"]["adresse"]
    etablissement = {
        # name=address["l1"],
        # # FIXME To check (l4 => line_1)
        # address_line_1=address["l4"],
        # address_line_2=address["l3"],
        # post_code=address["code_postal"],
        # city=address["localite"],
        # department=department_from_postcode(address["code_postal"]),
        "naf": data["etablissement"]["naf"],
        "is_closed": data["etablissement"]["etat_administratif"]["value"] == "F",
        "is_head_office": data["etablissement"].get("siege_social", False),
        "employees": data["etablissement"]["tranche_effectif_salarie_etablissement"]["intitule"],
        "employees_date_reference": data["etablissement"]["tranche_effectif_salarie_etablissement"]["date_reference"],
        "date_constitution": date.fromtimestamp(data["etablissement"]["date_creation_etablissement"]),
    }

    return etablissement, None


def siae_update_etablissement(siae):
    etablissement, error = etablissement_get_or_error(siae.siret, reason=API_ENTREPRISE_REASON)

    update_data = dict()

    if etablissement:
        # update_data"nature"] = Siae.NATURE_HEAD_OFFICE if etablissement["is_head_office"] else Siae.NATURE_ANTENNA  # noqa
        # update_data"is_active"] = False if not etablissement["is_closed"] else True
        if etablissement["employees"]:
            update_data["api_entreprise_employees"] = (
                etablissement["employees"]
                if (etablissement["employees"] != "Unités non employeuses")
                else "Non renseigné"
            )
        if etablissement["employees_date_reference"]:
            update_data["api_entreprise_employees_year_reference"] = etablissement["employees_date_reference"]
        if etablissement["date_constitution"]:
            update_data["api_entreprise_date_constitution"] = etablissement["date_constitution"]
    # else:
    #     self.stdout.write(error)
    # TODO: if 404, siret_is_valid = False ?

    update_data["api_entreprise_etablissement_last_sync_date"] = timezone.now()
    Siae.objects.filter(id=siae.id).update(**update_data)

    return 1 if etablissement else 0


def exercice_get_or_error(siret, reason="Inscription au marché de l'inclusion"):
    """
    Obtain company data from entreprises.api.gouv.fr
    documentation: https://entreprise.api.gouv.fr/catalogue/#a-exercices

    Format info:
    - "date_fin_exercice": "2016-12-31T00:00:00+01:00"

    Often returns errors: 404, 422, 502
    """
    data = None
    exercice = None
    error = None

    query_string = urlencode(
        {
            "recipient": settings.API_ENTREPRISE_RECIPIENT,
            "context": settings.API_ENTREPRISE_CONTEXT,
            "object": reason,
        }
    )

    url = f"{settings.API_ENTREPRISE_BASE_URL}/exercices/{siret}?{query_string}"
    headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}

    try:
        r = httpx.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            error = f"SIRET {siret} non reconnu."
        else:
            # logger.error("Error while fetching `%s`: %s", url, e)
            error = "Problème de connexion à la base Sirene. Essayez ultérieurement."
        return None, error
    except httpx.ReadTimeout as e:  # noqa
        # logger.error("Error while fetching `%s`: %s", url, e)
        error = "The read operation timed out"
        return None, error

    if data and data.get("errors"):
        error = data["errors"][0]
        return None, error

    if not data.get("exercices") or not len(data["exercices"]):
        # logger.error("Invalid format of response from API Entreprise")
        error = "Le format de la réponse API Entreprise est non valide."
        return None, error

    exercice = data["exercices"][0]

    return exercice, None


def siae_update_exercice(siae):
    exercice, error = exercice_get_or_error(siae.siret, reason=API_ENTREPRISE_REASON)  # noqa

    update_data = dict()

    if exercice:
        update_data = dict()
        if exercice["ca"]:
            update_data["api_entreprise_ca"] = exercice["ca"]
        if exercice["date_fin_exercice"]:
            update_data["api_entreprise_ca_date_fin_exercice"] = datetime.strptime(
                exercice["date_fin_exercice"][:-6], TIMESTAMP_FORMAT
            ).date()
    # else:
    #     self.stdout.write(error)

    update_data["api_entreprise_exercice_last_sync_date"] = timezone.now()
    Siae.objects.filter(id=siae.id).update(**update_data)

    return 1 if exercice else 0
