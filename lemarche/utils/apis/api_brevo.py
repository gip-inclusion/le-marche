import json
import logging
import time

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.tenders import constants as tender_constants
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX
from lemarche.utils.data import sanitize_to_send_by_email
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


def create_contact(user, list_id: int, tender=None):
    """
    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CreateContact.md
    - API: https://developers.brevo.com/reference/createcontact
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    attributes = {
        "NOM": sanitize_to_send_by_email(user.last_name.capitalize()),
        "PRENOM": sanitize_to_send_by_email(user.first_name.capitalize()),
        "DATE_INSCRIPTION": user.created_at,
        "TYPE_ORGANISATION": user.buyer_kind_detail,
        "NOM_ENTREPRISE": sanitize_to_send_by_email(user.company_name.capitalize()),
        "SMS": sanitize_to_send_by_email(user.phone_display),
        "MONTANT_BESOIN_ACHETEUR": None,
        "TYPE_BESOIN_ACHETEUR": None,
        "TYPE_VERTICALE_ACHETEUR": None,
        # WHATSAPP, TYPE_ORGANISATION, LIEN_FICHE_COMMERCIALE, TAUX_DE_COMPLETION
    }

    if tender:
        try:
            first_sector = tender.sectors.first()
            attributes["MONTANT_BESOIN_ACHETEUR"] = tender.amount_int
            attributes["TYPE_BESOIN_ACHETEUR"] = tender.kind

            # Check if there is one sector whose tender source is TALLY
            if tender.source == tender_constants.SOURCE_TALLY and first_sector:
                attributes["TYPE_VERTICALE_ACHETEUR"] = first_sector.name
            else:
                attributes["TYPE_VERTICALE_ACHETEUR"] = None

        except AttributeError as e:
            logger.error(f"Erreur d'attribut : {e}")
        except Exception as e:
            logger.error(f"Une erreur inattendue est survenue : {e}")

    new_contact = sib_api_v3_sdk.CreateContact(
        email=user.email,
        list_ids=[list_id],
        attributes=attributes,
        ext_id=str(user.id),
        update_enabled=True,
    )

    try:
        if not user.brevo_contact_id:
            api_response = api_instance.create_contact(new_contact).to_dict()
            user.brevo_contact_id = api_response.get("id")
            user.save()
            logger.info(f"Success Brevo->ContactsApi->create_contact: {api_response}")
        else:
            logger.info("User already exists in Brevo")
    except ApiException as e:
        logger.error(f"Exception when calling Brevo->ContactsApi->create_contact (list_id : {list_id}): {e.body}")


def update_contact(user_identifier: str, attributes_to_update: dict):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)
    update_contact = sib_api_v3_sdk.UpdateContact(attributes=attributes_to_update)
    try:
        api_response = api_instance.update_contact(identifier=user_identifier, update_contact=update_contact)
        logger.info(f"Success Brevo->ContactsApi->update_contact: {api_response}")
    except ApiException as e:
        logger.error(f"Exception when calling Brevo->ContactsApi->update_contact: {e}")


def update_contact_email_blacklisted(user_identifier: str, email_blacklisted: bool):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    update_contact = sib_api_v3_sdk.UpdateContact(email_blacklisted=email_blacklisted)
    try:
        api_response = api_instance.update_contact(identifier=user_identifier, update_contact=update_contact)
        logger.info(f"Success Brevo->ContactsApi->update_contact to update email_blacklisted: {api_response}")
    except ApiException as e:
        logger.error(f"Exception when calling Brevo->ContactsApi->update_contact to update email_blacklisted: {e}")


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
    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CompaniesApi.md
    - API: https://developers.brevo.com/reference/post_companies
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)

    siae_brevo_company_body = sib_api_v3_sdk.Body(
        name=siae.name,
        attributes={
            # default attributes
            # name, owner, linked_contacts, revenue, number_of_employees, created_at, last_updated_at, next_activity_date, owner_assign_date, number_of_contacts, number_of_activities, industry  # noqa
            "domain": siae.website,
            "phone_number": siae.contact_phone_display,
            # custom attributes
            "app_id": siae.id,
            "siae": True,
            "active": siae.is_active,
            "description": siae.description,
            "kind": siae.kind,
            "address_street": siae.address,
            "address_post_code": siae.post_code,
            "address_city": siae.city,
            "contact_email": siae.contact_email,
            "logo_url": siae.logo_url,
            "app_url": get_object_share_url(siae),
            "app_admin_url": get_object_admin_url(siae),
            "taux_de_completion": siae.extra_data.get("brevo_company_data", {}).get("completion_rate"),
            "nombre_de_besoins_recus": siae.extra_data.get("brevo_company_data", {}).get("tender_received"),
            "nombre_de_besoins_interesses": siae.extra_data.get("brevo_company_data", {}).get("tender_interest"),
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
            siae.brevo_company_id = api_response.id
            siae.save(update_fields=["brevo_company_id"])
        except ApiException as e:
            logger.error(f"Exception when calling Brevo->CompaniesApi->create_or_update_company (create): {e}")


def create_deal(tender, owner_email: str):
    """
    Creates a new deal in Brevo CRM from a tender and logs the result.

    This function configures a deal using the tender's details and the owner's email, and posts it to the Brevo CRM.
    If successful, it updates the tender with the new deal ID. If it encounters issues, it logs an error.

    Brevo docs
    - https://github.com/sendinblue/APIv3-python-library/blob/master/docs/DealsApi.md
    - https://developers.brevo.com/reference/post_crm-deals

    Args:
        tender (Tender): Object with tender details like title, description, amount, and deadlines.
        owner_email (str): The email address of the deal's owner.

    Raises:
        ApiException: If the Brevo API encounters an error during deal creation.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.DealsApi(api_client)
    body_deal = sib_api_v3_sdk.Body3(
        name=tender.title,
        attributes={
            # default attributes
            # pipeline, deal_stage, closed_won_reason, closed_lost_reason, total_revenue, lost_reason
            "deal_description": tender.description,
            "deal_owner": owner_email,
            "close_date": tender.deadline_date.strftime("%Y-%m-%d"),
            # custom attributes
            "amount": tender.amount_int,
            "tender_admin_url": tender.get_admin_url(),
        },
    )

    try:
        # create deal
        new_deal = api_instance.crm_deals_post(body_deal).to_dict()
        logger.info("Succes Brevo->Create a deal : %s\n" % new_deal)
        # save brevo deal id
        tender.brevo_deal_id = new_deal.get("id")
        tender.save()
    except ApiException as e:
        logger.error("Exception when calling Brevo->DealApi->create_deal: %s\n" % e)
        raise ApiException(e)


def link_deal_with_contact_list(tender, contact_list: list = None):
    """
    Links a Brevo deal to a list of contacts. If no contact list is provided, it defaults
    to linking the deal with the tender's author.

    This function uses the tender's stored deal ID and either a provided list of contact IDs or the
    tender author's contact ID to link contacts to the deal in the Brevo CRM.

    Args:
        tender (Tender): The tender object containing the Brevo deal ID and author's contact ID.
        contact_list (list of int, optional): List of contact IDs to be linked with the deal. Defaults to None.

    Raises:
        ApiException: If an error occurs during the linking process in the Brevo API.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.DealsApi(api_client)

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            # get brevo ids
            brevo_crm_deal_id = tender.brevo_deal_id
            # Default to the author's contact ID if no contact list is provided
            if not contact_list:
                contact_list = [tender.author.brevo_contact_id]

            # cleanup
            contact_list = [id for id in contact_list if id is not None]

            # link deal with contact_list
            if len(contact_list):
                # https://github.com/sendinblue/APIv3-python-library/blob/master/docs/Body5.md
                body_link_deal_contact = sib_api_v3_sdk.Body5(link_contact_ids=contact_list)
                api_instance.crm_deals_link_unlink_id_patch(brevo_crm_deal_id, body_link_deal_contact)

        except ApiException as e:
            logger.error("Exception when calling Brevo->DealApi->crm_deals_link_unlink_id_patch: %s\n" % e)


def link_company_with_contact_list(siae, contact_list: list = None):
    """
    Links a Brevo company to a list of contacts. If no contact list is provided, it defaults
    to linking the company with the siae's users.

    This function uses the siae's stored company ID and either a provided list of contact IDs or the
    siae author's user(s) ID(s) to link contacts to the company in the Brevo CRM.

    Args:
        siae (Siae): The siae object containing the Brevo company ID and author's contact ID.
        contact_list (list of int, optional): List of contact IDs to be linked with the company. Defaults to None.

    Raises:
        ApiException: If an error occurs during the linking process in the Brevo API.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            # get brevo ids
            brevo_crm_company_id = siae.brevo_company_id
            # Default to the siae's user(s) ID(s) if no contact list is provided
            if not contact_list:
                contact_list = list(siae.users.values_list("brevo_contact_id", flat=True))

            # cleanup
            contact_list = [id for id in contact_list if id is not None]

            # link company with contact_list
            if len(contact_list):
                # https://github.com/sendinblue/APIv3-python-library/blob/master/docs/Body2.md
                body_link_company_contact = sib_api_v3_sdk.Body2(link_contact_ids=contact_list)
                api_instance.companies_link_unlink_id_patch(brevo_crm_company_id, body_link_company_contact)

        except ApiException as e:
            logger.error("Exception when calling Brevo->DealApi->companies_link_unlink_id_patch: %s\n" % e)


def get_all_users_from_list(
    list_id: int = settings.BREVO_CL_SIGNUP_BUYER_ID, limit=500, offset=0, max_retries=3, verbose=False
):
    """
    Fetches all users from a specified Brevo CRM list, using pagination and retry strategies.

    Args:
        list_id (int): ID of the list to fetch users from. Defaults to BREVO_CL_SIGNUP_BUYER_ID.
        limit (int): Number of users to fetch per request. Defaults to 500.
        offset (int): Initial offset for fetching users. Defaults to 0.
        max_retries (int): Maximum number of retries on API failure. Defaults to 3.

    Returns:
        dict: Maps user emails to their IDs.

    Raises:
        ApiException: On API failures exceeding retry limit.
        Exception: On unexpected errors.

    This function attempts to retrieve all contacts from the given list and handles API errors
    by retrying up to `max_retries` times with exponential backoff.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)
    result = {}
    is_finished = False
    retry_count = 0
    while not is_finished:
        try:
            api_response = api_instance.get_contacts_from_list(list_id=list_id, limit=limit, offset=offset).to_dict()
            contacts = api_response.get("contacts", [])
            if verbose:
                logger.info(f"Contacts fetched: {len(contacts)} at offset {offset}")
            for contact in contacts:
                result[contact.get("email")] = contact.get("id")
            # Update the loop exit condition
            if len(contacts) < limit:
                is_finished = True
            else:
                offset += limit
        except ApiException as e:
            logger.error(f"Exception when calling ContactsApi->get_contacts_from_list: {e}")
            retry_count += 1
            if retry_count > max_retries:
                logger.error("Max retries exceeded. Exiting function.")
                break
            time.sleep(2**retry_count)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
    return result


@task()
def send_transactional_email_with_template(
    template_object,
    recipient_content_object,
    parent_content_object,
    template_id: int,
    recipient_email: str,
    recipient_name: str,
    variables: dict,
    subject=None,
    from_email=settings.DEFAULT_FROM_EMAIL,
    from_name=settings.DEFAULT_FROM_NAME,
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

    template_object.create_send_log(
        recipient_content_object=recipient_content_object,
        parent_content_object=parent_content_object,
        extra_data={"source": "fgfh"},  # "response": result()
    )

    logger.error("LOG CREATED")

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(**data)
            response = api_instance.send_transac_email(send_smtp_email)
            logger.error("Brevo: send transactional email with template")
            # {'message_id': '<202407151419.84958140835@smtp-relay.mailin.fr>', 'message_ids': None}
            return response.to_dict()
        except ApiException as e:
            logger.error(f"ApiException: {e}")
    else:
        logger.error("Brevo: email not sent (DEV or TEST environment detected)")
