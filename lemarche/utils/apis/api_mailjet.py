import logging

import requests
from django.conf import settings
from huey.contrib.djhuey import task


logger = logging.getLogger(__name__)


BASE_URL = "https://api.mailjet.com/v3/REST/"
SEND_URL = "https://api.mailjet.com/v3.1/send"


def contact_list_endpoint(contact_list_id):
    return f"{BASE_URL}contactslist/{contact_list_id}/managecontact"


def get_default_params():
    return {}


def get_default_client(params={}):
    params |= get_default_params()
    headers = {
        "user-agent": "betagouv-lemarche/0.0.1",
    }
    client = requests.Session()
    client.params = params
    client.headers = headers
    client.auth = (settings.MAILJET_MASTER_API_KEY, settings.MAILJET_MASTER_API_SECRET)
    return client


@task()
def add_to_contact_list_async(email_address, properties, contact_list_id, client=None):
    """
    Huey task adding contact to configured contact list

    Args:
        email_address (String): e-mail of contact
        properties (Dict): {"nom": "", "prénom": "", "pays": "france", "nomsiae": "", "poste": ""}
        contact_list_id (int): Mailjet id of contact list
        client (requests.Session, optional): client to send requests. Defaults to None.

    Raises:
        e: requests.HTTPStatusError
    """
    data = {
        "name": email_address,
        "properties": properties,
        "action": "addnoforce",
        "email": email_address,
    }
    if not client:
        client = get_default_client()

    try:
        response = client.post(contact_list_endpoint(contact_list_id), json=data)
        response.raise_for_status()
        logger.info("add user to contact list")
        logger.info(response.json())
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
        raise e


@task()
def send_transactional_email_with_template(
    template_id, subject, recipient_email, recipient_name, variables, client=None
):
    data = {
        "Messages": [
            {
                "From": {"Email": settings.DEFAULT_FROM_EMAIL, "Name": settings.DEFAULT_FROM_NAME},
                "To": [{"Email": recipient_email, "Name": recipient_name}],
                "TemplateID": template_id,
                "TemplateLanguage": True,
                "Subject": subject,
                "Variables": variables,
                # "Variables": {}
            }
        ]
    }
    if not client:
        client = get_default_client()

    if settings.BITOUBI_ENV != "dev":
        try:
            response = client.post(SEND_URL, json=data)
            response.raise_for_status()
            logger.info("Mailjet: send transactional email with template")
            logger.info(response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
    else:
        logger.info("Email not sent (DEV environment detected)")


@task()
def send_transactional_email_many_recipient_with_template(
    template_id, subject, recipient_email_list, variables, client=None
):
    data = {
        "Messages": [
            {
                "From": {"Email": settings.DEFAULT_FROM_EMAIL, "Name": settings.DEFAULT_FROM_NAME},
                "To": [{"Email": recipient_email} for recipient_email in recipient_email_list],
                "TemplateID": template_id,
                "TemplateLanguage": True,
                "Subject": subject,
                "Variables": variables,
                # "Variables": {}
            }
        ]
    }
    if not client:
        client = get_default_client()

    if settings.BITOUBI_ENV != "dev":
        try:
            response = client.post(SEND_URL, json=data)
            response.raise_for_status()
            logger.info("Mailjet: send transactional email with template")
            logger.info(response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
    else:
        logger.info("Email not sent (DEV environment detected)")
