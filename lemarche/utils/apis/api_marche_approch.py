import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


INFO_URL = "https://projets-achats.marches-publics.gouv.fr"
BASE_URL = "https://recette-portail-entreprises.fr/api/public/projects"

# FIELD_MAPPING = {
#     "title": "title",
#     "description": "description",
#     "external_link": "link",
#     "created_at": "pubDate"
# }
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2021-10-19T07:54:02.000Z"  # timezone not managed


def get_default_params():
    return {}


def get_default_client(params={}):
    params |= get_default_params()
    headers = {
        "user-agent": "betagouv-lemarche/0.0.1",
        "Authorization": f"Bearer {settings.MARCHE_APPROCH_TOKEN_RECETTE}",
    }
    client = requests.Session()
    client.params = params
    client.headers = headers

    return client


def get_offers_list(client=None):
    if not client:
        client = get_default_client()

    offer_list = []

    try:
        r = client.get(BASE_URL)
        r.raise_for_status()

        data = r.json()
        print(len(data["purchasingProjects"]))  # 961
        print(data["purchasingProjects"][0])

        for item in data:
            offer = {}

            offer_list.append(offer)

    except requests.exceptions.HTTPError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
