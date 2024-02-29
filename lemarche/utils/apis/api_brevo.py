import json
import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.siaes.models import Siae
from lemarche.users.models import User
from lemarche.utils.urls import get_object_admin_url, get_object_share_url


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
        logger.info(f"Success Brevo->ContactsApi->create_contact: {api_response}")
    except ApiException as e:
        logger.error(f"Exception when calling Brevo->ContactsApi->create_contact: {e}")


def remove_contact_from_list(user: User, list_id: int):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)
    contact_emails = sib_api_v3_sdk.RemoveContactFromList(emails=[user.email])

    try:
        api_response = api_instance.remove_contact_from_list(list_id=list_id, contact_emails=contact_emails)
        logger.info(f"Success Brevo->ContactsApi->remove_contact_from_list: {api_response}")
    except ApiException as e:
        error_body = json.loads(e.body)
        if error_body.get("message") == "Contact already removed from list and/or does not exist":
            logger.info("calling Brevo->ContactsApi->remove_contact_from_list: contact doesn't exist in this list")
        else:
            logger.error(f"Exception when calling Brevo->ContactsApi->remove_contact_from_list: {e}")


def create_or_update_company(siae: Siae):
    """
    Brevo docs:
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CompaniesApi.md
    - API: https://developers.brevo.com/reference/get_companies
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)

    siae_brevo_company_body = sib_api_v3_sdk.Body(
        name=siae.name,
        attributes={
            "app_id": siae.id,
            "siae": True,
            "active": siae.is_active,
            "description": siae.description,
            "kind": siae.kind,
            "address_street": siae.address,
            "address_post_code": siae.post_code,
            "address_city": siae.city,
            "contact_email": siae.contact_email,
            "contact_phone": siae.contact_phone,
            "domain": siae.website,
            "logo_url": siae.logo_url,
            "geo_range": siae.geo_range,
            "app_url": get_object_share_url(siae),
            "app_admin_url": get_object_admin_url(siae),
        },
    )

    if siae.brevo_company_id:  # update
        try:
            api_response = api_instance.companies_id_patch(siae.brevo_company_id, siae_brevo_company_body)
            # logger.info(f"Success Brevo->CompaniesApi->create_or_update_company (update): {api_response}")
            # api_response: {'attributes': None, 'id': None, 'linked_contacts_ids': None, 'linked_deals_ids': None}
        except ApiException as e:
            logger.error(f"Exception when calling Brevo->CompaniesApi->create_or_update_company (update): {e}")
    else:  # create
        try:
            api_response = api_instance.companies_post(siae_brevo_company_body)
            logger.info(f"Success Brevo->CompaniesApi->create_or_update_company (create): {api_response}")
            # api_response: {'id': '<brevo_company_id>'}
            siae.set_brevo_id(api_response.id)
        except ApiException as e:
            logger.error(f"Exception when calling Brevo->CompaniesApi->create_or_update_company (create): {e}")


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
            print(f"Exception when calling SMTPApi->send_transac_email: {e}")
    else:
        logger.info("Brevo: email not sent (DEV or TEST environment detected)")
