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
    client = httpx.Client(params=params, auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET))
    return client


def add_to_newsletter(user_id, email_adress, contact_list_id, client=None):
    # API is limited to 5000 calls per day
    # we pass the client to manage the case of many requests
    # client provide default params
    data = {"IsUnsubscribed": "false", "Contact": user_id, "ContactAlt": email_adress, "ListAlt": contact_list_id}

    if not client:
        client = get_default_client()

    try:
        r = client.post(contact_list_endpoint, data=data)
        r.raise_for_status()
        data = r.json()
        print(data)
        return data
    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
        raise e
