# https://github.com/betagouv/itou/blob/master/itou/utils/apis/api_entreprise.py

import logging
from datetime import date, datetime

import httpx
from django.utils import timezone
from django.utils.http import urlencode

from lemarche.siaes.models import Siae


logger = logging.getLogger(__name__)


API_QPV_REASON = "Mise à jour donnéés Marché de la plateforme de l'Inclusion"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed

BASE_URL = "https://equipements.sports.gouv.fr/api/records/1.0/search"
DATASET_QPV = "quartiers-prioritaires-de-la-politique-de-la-ville-qpv"
DISTANCE_TO_VALIDATE_QPV = 0

IS_QPV_KEY = "is_qpv"
QPV_NAME_KEY = "qpv_name"
QPV_CODE_KEY = "qpv_code"


def get_client():
    pass


def is_in_qpv(latitude, longitude, distance=DISTANCE_TO_VALIDATE_QPV, client=None):
    # we pass the client to manage the case of many requests
    client = httpx if not client else client
    params = {"dataset": DATASET_QPV, "geofilter.distance": f"{latitude},{longitude},{distance}"}

    try:
        r = client.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()
        records = data["records"]
        if records:
            qpv = records[0]
            return {IS_QPV_KEY: True, QPV_NAME_KEY: qpv["fields"]["nom_qp"], QPV_CODE_KEY: qpv["fields"]["code_qp"]}
        return {IS_QPV_KEY: False}
    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
        raise e
