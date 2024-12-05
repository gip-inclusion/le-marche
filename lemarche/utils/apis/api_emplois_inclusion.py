import logging
import time

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


# Doc : https://emplois.inclusion.beta.gouv.fr/api/v1/redoc/#tag/marche/operation/marche_list
API_ENDPOINT = f"{settings.API_EMPLOIS_INCLUSION_URL}/marche"
API_HEADERS = {"Authorization": f"Token {settings.API_EMPLOIS_INCLUSION_TOKEN}"}


def get_siae_list():
    siae_list = list()
    pagination = 1

    # loop on API to fetch all the data
    while True:
        API_URL = f"{API_ENDPOINT}?page={pagination}&page_size={1000}"
        logger.info(API_URL)
        response = requests.get(API_URL, headers=API_HEADERS)
        data = response.json()
        if data["results"]:
            for siae in data["results"]:
                siae_list.append(siae)
        if data["next"]:
            pagination += 1
            time.sleep(1)
        else:
            break

    return siae_list
