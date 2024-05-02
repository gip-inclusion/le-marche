import json
import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.tenders.constants import AMOUNT_RANGE_CHOICE_EXACT
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX
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


def create_contact(user, list_id: int):
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


def remove_contact_from_list(user, list_id: int):
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


def create_or_update_company(siae):
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
    recipient_email: str,
    recipient_name: str,
    variables: dict,
    subject: str,
    from_email: str,
    from_name: str,
):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
    data = {
        "sender": {"email": from_email, "name": from_name},
        "to": [{"email": recipient_email, "name": recipient_name}],
        "template_id": template_id,
        "params": variables,
    }
    # if subject empty, defaults to Brevo's template subject
    if subject:
        data["subject"] = EMAIL_SUBJECT_PREFIX + subject

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(**data)
            response = api_instance.send_transac_email(send_smtp_email)
            logger.info("Brevo: send transactional email with template")
            return response
        except ApiException as e:
            print(f"Exception when calling SMTPApi->send_transac_email: {e}")
    else:
        logger.info("Brevo: email not sent (DEV or TEST environment detected)")


def create_deal(tender, owner_email: str):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.DealsApi(api_client)
    body = sib_api_v3_sdk.Body3(
        name=tender.title,
        attributes={
            "deal_description": tender.description,
            # "deal_pipeline": "...",
            # "deal_stage": "...",
            "deal_owner": owner_email,
            "amount": AMOUNT_RANGE_CHOICE_EXACT.get(tender.amount, 0),
            "tender_admin_url": tender.get_admin_url(),
            "close_date": tender.deadline_date.strftime("%Y-%m-%d"),
        },
    )

    try:
        # create deal
        new_deal = api_instance.crm_deals_post(body).to_dict()
        logger.info("Succes Brevo->Create a deal : %s\n" % new_deal)
        # save brevo deal id
        tender.crm_id = new_deal.get("id")
        tender.save()
    except ApiException as e:
        logger.error("Exception when calling Brevo->DealApi->create_deal: %s\n" % e)


def link_deal_with_list_contact(tender, contact_list: list = None):
    """Link brevo deal with contact list
    Args:
        tender (_type_): Tender to link
        contact_list (list<int>, optional): List integer of brevo contact ids. Defaults to None.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.DealsApi(api_client)

    try:
        # get brevo ids
        brevo_crm_deal_id = tender.crm_id
        brevo_crm_author_deal_id = tender.author.crm_id
        if not contact_list:
            contact_list = [brevo_crm_author_deal_id]
        # link deal with author
        # https://github.com/sendinblue/APIv3-python-library/blob/master/docs/Body5.md
        body = sib_api_v3_sdk.Body5(link_contact_ids=[int(brevo_crm_author_deal_id)])
        api_instance.crm_deals_link_unlink_id_patch(brevo_crm_deal_id, body)

    except ApiException as e:
        logger.error("Exception when calling Brevo->DealApi->crm_deals_link_unlink_id_patch: %s\n" % e)
