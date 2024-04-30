import logging

import requests
from django.conf import settings
from huey.contrib.djhuey import task

from lemarche.users import constants as user_constants
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX


logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")
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


def get_mailjet_cl_on_signup(user, source: str = user_constants.SOURCE_SIGNUP_FORM):
    if user.kind == user_constants.KIND_SIAE:
        return settings.MAILJET_NL_CL_SIAE_ID
    elif user.kind == user_constants.KIND_BUYER:
        if source == user_constants.SOURCE_SIGNUP_FORM:
            return settings.MAILJET_NL_CL_BUYER_ID
        elif source == user_constants.SOURCE_TALLY_FORM:
            return settings.MAILJET_NL_CL_BUYER_TALLY_ID
        elif source == user_constants.SOURCE_TENDER_FORM:
            return settings.MAILJET_NL_CL_BUYER_TENDER_ID
    elif user.kind == user_constants.KIND_PARTNER:
        if user.partner_kind == user_constants.PARTNER_KIND_FACILITATOR:
            return settings.MAILJET_NL_CL_PARTNER_FACILITATORS_ID
        elif user.partner_kind in (
            user_constants.PARTNER_KIND_NETWORD_IAE,
            user_constants.PARTNER_KIND_NETWORK_HANDICAP,
        ):
            return settings.MAILJET_NL_CL_PARTNER_NETWORKS_IAE_HANDICAP_ID
        elif user.partner_kind == user_constants.PARTNER_KIND_DREETS:
            return settings.MAILJET_NL_CL_PARTNER_DREETS_ID


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

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            response = client.post(contact_list_endpoint(contact_list_id), json=data)
            response.raise_for_status()
            logger.info("Mailjet: add user to contact list")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
    else:
        logger.info("Mailjet: not add contact in contact list (DEV or TEST environment detected)")


@task()
def send_transactional_email_with_template(
    template_id: int,
    recipient_email: str,
    recipient_name: str,
    variables: dict,
    subject: str,
    from_email: str,
    from_name: str,
    client=None,
):
    data = {
        "Messages": [
            {
                "From": {"Email": from_email, "Name": from_name},
                "To": [{"Email": recipient_email, "Name": recipient_name}],
                "TemplateID": template_id,
                "TemplateLanguage": True,
                "Variables": variables,
            }
        ]
    }
    # if subject empty, defaults to Mailjet's template subject
    if subject:
        data["Messages"][0]["Subject"] = EMAIL_SUBJECT_PREFIX + subject

    if not client:
        client = get_default_client()

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            response = client.post(SEND_URL, json=data)
            response.raise_for_status()
            logger.info("Mailjet: send transactional email with template")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
    else:
        logger.info("Mailjet: email not sent (DEV or TEST environment detected)")


@task()
def send_transactional_email_many_recipient_with_template(
    template_id,
    subject,
    recipient_email_list,
    variables,
    from_email=settings.DEFAULT_FROM_EMAIL,
    from_name=settings.DEFAULT_FROM_NAME,
    client=None,
):
    data = {
        "Messages": [
            {
                "From": {"Email": from_email, "Name": from_name},
                "To": [{"Email": recipient_email} for recipient_email in recipient_email_list],
                "TemplateID": template_id,
                "TemplateLanguage": True,
                "Subject": EMAIL_SUBJECT_PREFIX + subject,
                "Variables": variables,
                # "Variables": {}
            }
        ]
    }
    if not client:
        client = get_default_client()

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            response = client.post(SEND_URL, json=data)
            response.raise_for_status()
            logger.info("Mailjet: send transactional email (multiple recipients) with template")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
    else:
        logger.info("Mailjet: email not sent (DEV environment detected)")
