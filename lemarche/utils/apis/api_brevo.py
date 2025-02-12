import logging
import time
from typing import Any, Dict, Optional

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.tenders import constants as tender_constants
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX
from lemarche.utils.data import sanitize_to_send_by_email

logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")


def get_config():
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY
    return config


def get_api_client():
    config = get_config()
    return sib_api_v3_sdk.ApiClient(config)


def create_contact(user, list_id: int, tender=None) -> None:
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


def update_contact_email_blacklisted(user_identifier: str, email_blacklisted: bool):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    update_contact = sib_api_v3_sdk.UpdateContact(email_blacklisted=email_blacklisted)
    try:
        api_response = api_instance.update_contact(identifier=user_identifier, update_contact=update_contact)
        logger.info(f"Success Brevo->ContactsApi->update_contact to update email_blacklisted: {api_response}")
    except ApiException as e:
        logger.error(f"Exception when calling Brevo->ContactsApi->update_contact to update email_blacklisted: {e}")


def create_brevo_company_from_company(company) -> None:
    """
    Creates a Brevo company from a Company instance.

    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CompaniesApi.md
    - API: https://developers.brevo.com/reference/post_companies
    """
    create_company(company)


def create_brevo_company_from_siae(siae) -> None:
    """
    Creates a Brevo company from a Siae instance.

    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CompaniesApi.md
    - API: https://developers.brevo.com/reference/post_companies
    """
    create_company(siae)


def create_company(company_or_siae) -> None:
    """
    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CompaniesApi.md
    - API: https://developers.brevo.com/reference/post_companies

    Args:
        company_or_siae: instance to create in Brevo
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)

    # Determine if this is a SIAE
    from lemarche.siaes.models import Siae

    is_siae = isinstance(company_or_siae, Siae)

    company_data = sib_api_v3_sdk.Body(
        name=company_or_siae.name,
        attributes={
            "domain": company_or_siae.website if hasattr(company_or_siae, "website") else "",
            "app_id": company_or_siae.id,
            "siae": is_siae,
        },
    )

    if not company_or_siae.brevo_company_id:
        try:
            api_response = api_instance.companies_post(company_data)
            logger.info(f"Success Brevo->CompaniesApi->create_company (create): {api_response}")
            company_or_siae.brevo_company_id = api_response.id
            company_or_siae.save(update_fields=["brevo_company_id"])
        except ApiException as e:
            logger.error(f"Exception when calling Brevo->CompaniesApi->create_company (create): {e}")


def create_deal(tender) -> None:
    """
    Creates a new deal in Brevo CRM from a tender and logs the result.

    This function configures a deal using the tender's details and the owner's email, and posts it to the Brevo CRM.
    If successful, it updates the tender with the new deal ID. If it encounters issues, it logs an error.

    Brevo docs
    - https://github.com/sendinblue/APIv3-python-library/blob/master/docs/DealsApi.md
    - https://developers.brevo.com/reference/post_crm-deals

    Args:
        tender (Tender): Object with tender details like title, description, and deadlines.

    Raises:
        ApiException: If the Brevo API encounters an error during deal creation.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.DealsApi(api_client)
    attributes = {
        "deal_description": tender.description,
    }
    if tender.deadline_date:
        attributes["close_date"] = tender.deadline_date.strftime("%Y-%m-%d")
    body_deal = sib_api_v3_sdk.Body3(
        name=tender.title,
        attributes=attributes,
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


def link_company_with_contact_list(siae, contact_list=None):
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
    list_id: int = settings.BREVO_CL_SIGNUP_BUYER_ID,
    limit: int = 500,
    offset: int = 0,
    max_retries: int = 3,
    verbose: bool = False,
) -> Dict[str, int]:
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
    template_id: int,
    recipient_email: str,
    recipient_name: str,
    variables: Dict[str, Any],
    subject: Optional[str] = None,
    from_email: str = settings.DEFAULT_FROM_EMAIL,
    from_name: str = settings.DEFAULT_FROM_NAME,
) -> Optional[Dict[str, Any]]:
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
            # {'message_id': '<202407151419.84958140835@smtp-relay.mailin.fr>', 'message_ids': None}
            return response.to_dict()
        except ApiException as e:
            print(f"Exception when calling SMTPApi->send_transac_email: {e}")
    else:
        logger.info("Brevo: email not sent (DEV or TEST environment detected)")
