import json
import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.users.models import User


logger = logging.getLogger(__name__)


def get_brevo_config():
    brevo_configuration = sib_api_v3_sdk.Configuration()
    brevo_configuration.api_key["api-key"] = settings.BREVO_API_KEY
    return brevo_configuration


def get_api_client():
    brevo_config = get_brevo_config()
    return sib_api_v3_sdk.ApiClient(brevo_config)


ENV_NOT_ALLOWED = ("dev", "test")


@task()
def send_html_email(to: list, sender: dict, html_content: str, headers: dict = {}):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to, headers=headers, html_content=html_content, sender=sender
    )  # SendSmtpEmail | Values to send a transactional email
    try:
        # Send a transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


@task()
def send_transactionnel_email(to: list, sender: dict, template_id: int, params_template: dict, headers: dict = {}):
    """Send transactionnel email

    Args:
        to (list): List of dict, ex : [{"email": "testmail@example.com", "name": "John Doe"}]
        template_id (int): template id of email
        params_template (dict): Paramaters of template, ec {"name": "John", "surname": "Doe"}
        headers (dict, optional): Custom headers of emails. Defaults to {}.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to, template_id=template_id, sender=sender, params=params_template, headers=headers
    )  # SendSmtpEmail | Values to send a transactional email
    try:
        # Send a transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


def create_contact(user: User, list_id: int):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)
    new_contact = sib_api_v3_sdk.CreateContact(
        email=user.email,
        list_ids=[list_id],
        attributes={
            "NOM": user.first_name,
            "PRENOM": user.last_name,
            "DATE_INSCRIPTION": user.created_at,
            "TYPE_ORGANISATION": user.buyer_kind_detail,
            "NOM_ENTREPRISE": user.company_name,
        },
        ext_id=str(user.id),
        update_enabled=True,
    )

    try:
        api_response = api_instance.create_contact(new_contact)
        logger.info("Succes Brevo->ContactsApi->create_contact: %s\n" % api_response)
    except ApiException as e:
        logger.error("Exception when calling Brevo->ContactsApi->create_contact: %s\n" % e)


def remove_contact_from_list(user: User, list_id: int):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)
    contact_emails = sib_api_v3_sdk.RemoveContactFromList(emails=[user.email])

    try:
        api_response = api_instance.remove_contact_from_list(list_id=list_id, contact_emails=contact_emails)
        logger.info("Succes Brevo->ContactsApi->remove_contact_from_list: %s\n" % api_response)
    except ApiException as e:
        error_body = json.loads(e.body)
        if error_body.get("message") == "Contact already removed from list and/or does not exist":
            logger.info("calling Brevo->ContactsApi->remove_contact_from_list: contact doesn't exist in this list")
        else:
            logger.error("Exception when calling Brevo->ContactsApi->remove_contact_from_list: %s\n" % e)
