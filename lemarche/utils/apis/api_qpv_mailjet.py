# https://github.com/betagouv/itou/blob/master/itou/utils/apis/api_entreprise.py

import logging

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)


BASE_URL = "https://api.mailjet.com/v3/REST/"


def get_endpoint_url(endpoint):
    return f"{BASE_URL}{endpoint}"


contact_list_endpoint = get_endpoint_url(
    f"contactslist/{settings.MAILJET_NEWSLETTER_CONTACT_LIST_BUYER_ID}/managecontact"
)


def get_default_params():
    return {}


def get_default_client(params={}):
    params |= get_default_params()
    headers = {
        "user-agent": "betagouv-lemarche/0.0.1",
    }
    client = httpx.Client(params=params, headers=headers, auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET))
    return client


def add_to_newsletter(email_adress, properties, client=None):
    data = {
        "name": email_adress,
        "properties": properties,
        "action": "addnoforce",
        "email": email_adress,
    }

    if not client:
        client = get_default_client()

    try:
        result = client.post(contact_list_endpoint, json=data)
        result.raise_for_status()
        data = result.json()
        print(data)
        return data
    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
        raise e


# prop = {"nom": "Madjid", "prénom": "Madjid", "pays": "france", "nomsiae": "", "poste": ""}
