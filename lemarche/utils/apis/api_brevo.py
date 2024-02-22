import json
import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.siaes.models import Siae
from lemarche.users.models import User
from lemarche.utils.urls import get_admin_url_object, get_share_url_object


logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")


def get_config():
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY
    return config


def get_api_client():
    config = get_config()
    return sib_api_v3_sdk.ApiClient(config)


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


def create_company(siae: Siae):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)
    new_company = sib_api_v3_sdk.Body(
        name=siae.name,
        attributes={
            "id": siae.id,
            "siae": True,
            "description": siae.description,
            "kind": siae.kind,
            "domain": siae.website,
            "contact_email": siae.contact_email,
            "contact_phone": siae.contact_phone,
            "logo_url": siae.logo_url,
            "geo_range": siae.geo_range,
            "app_url": get_share_url_object(siae),
            "admin_url": get_admin_url_object(siae),
        },
    )

    try:
        api_response = api_instance.companies_post(new_company)
        logger.info("Succes Brevo->CompaniesApi->create_company: %s\n" % api_response)
    except ApiException as e:
        logger.error("Exception when calling Brevo->CompaniesApi->create_company: %s\n" % e)


@task()
def send_transactional_email_with_template(
    template_id: int,
    subject: str,
    recipient_email: str,
    recipient_name: str,
    variables: dict,
    from_email=settings.DEFAULT_FROM_EMAIL,
    from_name=settings.DEFAULT_FROM_NAME,
):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"email": from_email, "name": from_name},
        to=[{"email": recipient_email, "name": recipient_name}],
        subject=subject,
        template_id=template_id,
        params=variables,
    )

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            response = api_instance.send_transac_email(send_smtp_email)
            logger.info("Brevo: send transactional email with template")
            return response
        except ApiException as e:
            print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
    else:
        logger.info("Brevo: email not sent (DEV or TEST environment detected)")
