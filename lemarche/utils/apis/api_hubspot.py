import logging
import re

from django.conf import settings
from hubspot import Client
from hubspot.crm.contacts import ApiException, SimplePublicObject, SimplePublicObjectInput

from lemarche.tenders.models import Tender
from lemarche.users.models import User


# from huey.contrib.djhuey import task


logger = logging.getLogger(__name__)


BASE_URL = "https://api.hubapi.com/crm/v3/"


def get_default_client():
    client = Client.create(access_token=settings.HUBSPOT_API_KEY)
    return client


ENV_NOT_ALLOWED = (
    "dev",
    "test",
    "staging",
)


def add_to_contacts(
    email: str, company: str, firstname: str, lastname: str, phone: str, website: str, client: Client = None
):
    """Huey task adding contact to Hubspot CRM

    Args:
        email (str)
        company (str)
        firstname (str)
        lastname (str)
        phone (str)
        website (str)
        client (Client, optional): HubspotClient. Defaults to None.

    Raises:
        e: ApiException

    Returns:
        _type_: _description_
    """
    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED or settings.HUBSPOT_IS_ACTIVATED:
        if not client:
            client = get_default_client()
        try:
            properties = {
                "company": company,
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "phone": phone,
                "website": website,
            }
            simple_public_object_input = SimplePublicObjectInput(properties=properties)
            api_response = client.crm.contacts.basic_api.create(simple_public_object_input=simple_public_object_input)
            logger.info(f"User {email} added in hubpsot crm")
            return api_response
        except ApiException as e:
            if e.status == 409:  # conflict error
                # message error body is like this :
                # '{"status":"error","message":"Contact already exists. Existing ID: 8853",
                #    "correlationId":"9dfc8","category":"CONFLICT"}'
                # so we transforme the message from str to dict to get back the ID from hubspot crm
                dict_error = eval(e.body)
                regex_hubspot_contact_id = re.search(r"\d+", dict_error.get("message", ""))
                if regex_hubspot_contact_id:
                    hubspot_contact_id = regex_hubspot_contact_id.group()
                    logger.info(f"User {email} already exist in hubpsot crm")
                    return SimplePublicObject(id=hubspot_contact_id)
            else:
                logger.error("Exception when calling hubspot_api->create: %s\n" % e)
    else:
        logger.info("Hubspot: not add contact to the crm (STAGING or TEST environment detected)")


def add_user_to_crm(user: User):
    result = add_to_contacts(
        email=user.email,
        company=user.company_name,
        firstname=user.first_name,
        lastname=user.last_name,
        phone=user.phone,
        website=user.c4_website,
    )
    if result and result.id:
        user.set_hubspot_id(hubspot_contact_id=result.id, with_save=True)
    return result


# @task
def create_deal_from_tender(tender: Tender):
    tender_author_hubspot_contact_id = tender.author.hubspot_contact_id
    if not tender_author_hubspot_contact_id:
        user_added_in_crm = add_user_to_crm(tender.author)
        if user_added_in_crm and user_added_in_crm.id:
            tender_author_hubspot_contact_id = user_added_in_crm.id

    result = create_deal(tender_author_hubspot_contact_id=tender_author_hubspot_contact_id, dealname=tender.title)
    if result and result.id:
        tender.set_hubspot_id(hubspot_deal_id=result.id, with_save=True)


def create_deal(tender_author_hubspot_contact_id: str, dealname: str, client: Client = None):
    """Huey task adding contact to Hubspot CRM

    Args:
        tender_author_hubspot_contact_id (str)
        dealname (str)
        client (Client, optional): HubspotClient. Defaults to None.

    Raises:
        e: ApiException

    Returns:
        _type_: _description_
    """
    if not client:
        client = get_default_client()
    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED or settings.HUBSPOT_IS_ACTIVATED:
        try:
            properties = {
                # "amount": amount,
                # "closedate": closedate,
                "dealname": dealname,
                # will be "Dépôt de besoin" in Hubspot
                "dealstage": "presentationscheduled",
                # "pipeline": pipeline,
            }
            deal_encapsulated = SimplePublicObjectInput(properties=properties)
            api_deal_response: SimplePublicObject = client.crm.deals.basic_api.create(
                simple_public_object_input=deal_encapsulated
            )
            if api_deal_response and api_deal_response.id:
                api_deal_association_response: SimplePublicObject = client.crm.deals.associations_api.create(
                    deal_id=api_deal_response.id,
                    to_object_type="contacts",
                    to_object_id=tender_author_hubspot_contact_id,
                    association_type="deal_to_contact",
                )
                logger.info(api_deal_association_response)
            return api_deal_response
        except ApiException as e:
            if e.status == 409:  # conflict error
                logger.info(f"Deal {dealname} already exist in hubpsot crm")
            else:
                logger.error("Exception when calling hubspot_api->create: %s\n" % e)
    else:
        logger.info("Hubspot: not add contact to the crm (STAGING or TEST environment detected)")
