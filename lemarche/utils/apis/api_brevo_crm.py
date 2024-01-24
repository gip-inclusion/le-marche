import json
import logging

import sib_api_v3_sdk
from django.conf import settings

# from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender
from lemarche.users.models import User


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


def create_deal(tender: Tender):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.DealsApi(api_client)
    body = sib_api_v3_sdk.Body3(
        name=tender.title,
        attributes={
            # "deal_name": tender.title,
            "deal_description": tender.description,
            "deal_stage": "8cd08f5f-1914-4823-a1f6-88b4fe22071d",
            "amount": tender_constants.AMOUNT_RANGE_TO_MAX_INT.get(tender.amount, 0),
        },
    )  # Body3 | Deal create data.

    try:
        new_deal = api_instance.crm_deals_post(body)
        logger.info("Succes Brevo->Create a deal : %s\n" % new_deal)
    except ApiException as e:
        logger.error("Exception when calling Brevo->ContactsApi->create_contact: %s\n" % e)
