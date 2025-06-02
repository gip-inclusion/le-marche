import json
import logging
import time
from datetime import datetime, timedelta

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.tenders.enums import TenderSourcesChoices
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX
from lemarche.utils.data import sanitize_to_send_by_email
from lemarche.utils.urls import get_object_admin_url, get_object_share_url


logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")


class BrevoApiError(Exception):
    """Exception raised when contacts fetching fails after all retries"""

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)


class ContactsFetchError(BrevoApiError):
    """Exception raised when contacts fetching fails after all retries"""

    pass


class ContactCreationError(BrevoApiError):
    """Exception raised when contact creation fails after all retries"""

    pass


class CompanySyncError(BrevoApiError):
    """Exception raised when company synchronization fails after all retries"""

    pass


class ContactRetrievalError(BrevoApiError):
    """Exception raised when contact retrieval by email fails"""

    pass


def handle_api_retry(exception: ApiException, attempt, max_retries, retry_delay, operation_name, entity_id=""):
    """
    Helper function to handle API retry logic with exponential backoff

    Args:
        exception: The API exception that occurred
        attempt: Current attempt number (0-based)
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay in seconds between attempts
        operation_name: Name of the operation for logging
        entity_id (optional): ID of the entity being processed
        defaults to an empty string

    Returns:
        tuple: (should_retry: bool, wait_time: int)
    """
    if exception.status == 429:  # Rate limiting
        wait_time = retry_delay * (attempt + 1) * 2
        logger.warning(f"Rate limit reached while {operation_name} {entity_id}, waiting {wait_time}s")
        return True, wait_time

    # For other errors
    if attempt < max_retries:
        wait_time = retry_delay * (attempt + 1)
        logger.warning(
            f"Error {operation_name} {entity_id}, attempt {attempt+1}/{max_retries} in {wait_time}s: {exception}"
        )
        return True, wait_time
    else:
        logger.error(f"Failed after {max_retries} attempts to {operation_name} {entity_id}: {exception}")
        return False, 0


def _get_error_body(exception):
    """
    Helper function to extract error body from ApiException

    Args:
        exception: The ApiException object

    Returns:
        dict: Parsed error body or empty dict if parsing fails
    """
    try:
        if exception.body:  # Check if body is not None
            return json.loads(exception.body)
    except (json.JSONDecodeError, AttributeError):
        logger.error(
            f"Error decoding JSON response: {exception.body if hasattr(exception, 'body') else str(exception)}"
        )
    return {}


def get_config():
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY
    return config


def get_api_client():
    config = get_config()
    return sib_api_v3_sdk.ApiClient(config)


def _fetch_contacts_page(api_instance, limit, offset, modified_since):
    """
    Fetches a single page of contacts from Brevo API

    Args:
        api_instance: Brevo ContactsApi instance
        limit: Number of contacts to fetch
        offset: Offset for pagination
        modified_since: Date filter for modifications

    Returns:
        tuple: (list: List of contacts from the API response, int: Total count of contacts)
    """
    api_response = api_instance.get_contacts(limit=limit, offset=offset, modified_since=modified_since).to_dict()
    return api_response.get("contacts", []), api_response.get("count", 0)


def _should_continue_pagination(contacts_count, current_limit, total_retrieved, limit_max):
    """
    Determines if pagination should continue

    Args:
        contacts_count: Number of contacts in current page
        current_limit: Current page limit
        total_retrieved: Total contacts retrieved so far
        limit_max: Maximum limit (if specified)

    Returns:
        bool: Whether to continue pagination
    """
    # Si limit_max est défini et qu'on l'a atteint, on s'arrête
    if limit_max is not None and total_retrieved >= limit_max:
        return False

    # Si on a reçu moins de contacts que demandé, c'est qu'on a atteint la fin
    if contacts_count < current_limit:
        return False

    return True


def _calculate_current_limit(limit_max, total_retrieved, page_limit):
    """
    Calculates the limit for current API request

    Args:
        limit_max: Maximum total contacts to retrieve
        total_retrieved: Contacts already retrieved
        page_limit: Default page size

    Returns:
        int: Limit for current request
    """
    if limit_max is not None and total_retrieved + page_limit > limit_max:
        return limit_max - total_retrieved
    return page_limit


def get_all_contacts(limit_max=None, since_days=30, max_retries=3, retry_delay=5, page_limit=500):
    """
    Retrieves all contacts from Brevo, with optional filtering by modification date
    and limiting the total number of contacts returned.

    Args:
        limit_max (int, optional): Maximum number of contacts to retrieve in total.
            If None, retrieves all available contacts. Defaults to None.
        since_days (int, optional): Retrieve only contacts modified in the last X days.
            Defaults to 30.
        max_retries (int, optional): Maximum number of retry attempts in case of API errors.
            Defaults to 3.
        retry_delay (int, optional): Delay in seconds between retry attempts.
            Defaults to 5.
        page_limit (int, optional): Number of contacts to retrieve per API call.
            Defaults to 500.

    Returns:
        dict: Dictionary mapping contact emails to their IDs

    Raises:
        ContactsFetchError: When contacts fetching fails after all retries
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    config = _initialize_contacts_config(limit_max, since_days, page_limit)

    try:
        while not config["is_finished"]:
            _fetch_contacts_batch(api_instance, config, max_retries, retry_delay)
    except ContactsFetchError:
        # Error occurred and max retries exceeded
        pass

    logger.debug(f"Total contacts retrieved: {config['total_retrieved']}")

    return config["result"]


def _initialize_contacts_config(limit_max, since_days, page_limit):
    """Initialize configuration for contact fetching"""
    config = {
        "offset": 0,
        "modified_since": datetime.now() - timedelta(days=since_days),
        "result": {},
        "total_retrieved": 0,
        "is_finished": False,
        "retry_count": 0,
        "limit_max": limit_max,
        "page_limit": page_limit,
    }

    logger.debug(f"Retrieving contacts modified in the last {since_days} days")

    return config


def _fetch_contacts_batch(api_instance, config, max_retries, retry_delay):
    """
    Fetch a single batch of contacts with error handling

    Args:
        api_instance: Brevo ContactsApi instance
        config: Configuration dictionary for contact fetching
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries

    Raises:
        ContactsFetchError: When fetching fails after all retries
    """
    try:
        _process_contacts_batch(api_instance, config)
    except ApiException as e:
        _handle_contacts_api_error(e, config, max_retries, retry_delay)
    except Exception as e:
        logger.error(f"Unexpected error retrieving contacts: {e}")
        raise ContactsFetchError(f"Unexpected error retrieving contacts: {e}", e)


def _process_contacts_batch(api_instance, config):
    """
    Process a single batch of contacts

    Args:
        api_instance: Brevo ContactsApi instance
        config: Configuration dictionary for contact fetching

    Raises:
        None: Simply updates the config and marks pagination as finished when complete
    """
    current_limit = _calculate_current_limit(config["limit_max"], config["total_retrieved"], config["page_limit"])

    if current_limit <= 0:
        config["is_finished"] = True
        return

    logger.debug(f"Fetching contacts: limit={current_limit}, offset={config['offset']}")

    contacts, total_count_users = _fetch_contacts_page(
        api_instance, current_limit, config["offset"], config["modified_since"]
    )

    logger.debug(f"Retrieved {len(contacts)}/{total_count_users} contacts")

    # Process retrieved contacts
    for contact in contacts:
        config["result"][contact.get("email")] = contact.get("id")

    config["total_retrieved"] += len(contacts)

    # Determine if we should continue pagination
    config["is_finished"] = not _should_continue_pagination(
        len(contacts), current_limit, config["total_retrieved"], config["limit_max"]
    )

    if not config["is_finished"]:
        config["offset"] += current_limit

    # Reset retry counter on successful request
    config["retry_count"] = 0


def _handle_contacts_api_error(exception, config, max_retries, retry_delay):
    """
    Handle API errors during contact fetching

    Args:
        exception: The API exception that occurred
        config: Configuration dictionary for contact fetching
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries

    Raises:
        ContactsFetchError: When max retries are exceeded
    """
    logger.error(f"Exception when calling ContactsApi->get_contacts: {exception}")

    should_retry, wait_time = handle_api_retry(
        exception, config["retry_count"], max_retries, retry_delay, "get all contacts"
    )

    if should_retry:
        config["retry_count"] += 1
        logger.debug(f"Attempt {config['retry_count']}/{max_retries} failed, retrying in {wait_time}s...")
        time.sleep(wait_time)
        # Continue by not raising an exception
    else:
        logger.error(f"Failed after {max_retries} attempts for get all contacts")
        config["result"] = {}
        raise ContactsFetchError(f"Failed after {max_retries} attempts for get all contacts", exception)


def _additional_tender_attributes(tender):
    """
    Helper function to get additional attributes for a tender
    Args:
        tender: Tender object to extract attributes from

    Returns:
        dict: Dictionary of additional attributes for the tender
    """
    try:
        first_sector = tender.sectors.first()
        attributes = {
            "MONTANT_BESOIN_ACHETEUR": tender.amount_int,
            "TYPE_BESOIN_ACHETEUR": tender.kind,
        }

        # Check if there is one sector whose tender source is TALLY
        if tender.source == tender_constants.SOURCE_TALLY and first_sector:
            attributes["TYPE_VERTICALE_ACHETEUR"] = first_sector.name
        else:
            attributes["TYPE_VERTICALE_ACHETEUR"] = None

        return attributes

    except AttributeError as e:
        logger.error(f"Attribute error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    # Return default values only if an exception occurred
    return {
        "MONTANT_BESOIN_ACHETEUR": None,
        "TYPE_BESOIN_ACHETEUR": None,
        "TYPE_VERTICALE_ACHETEUR": None,
    }


def create_contact(user, list_id: int, tender=None, max_retries=3, retry_delay=5):
    """
    Create or update a contact in Brevo

    Args:
        user: User object to send to Brevo
        list_id (int): Brevo list ID to add the contact to
        tender: Tender object associated with the user (optional)
        max_retries (int): Maximum number of retry attempts in case of error
        retry_delay (int): Delay in seconds between retry attempts

    Raises:
        ContactCreationError: When contact creation fails after all retries
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    attributes: dict[str, str | None] = {
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
        attributes |= _additional_tender_attributes(tender)

    new_contact = sib_api_v3_sdk.CreateContact(
        email=user.email,
        list_ids=[list_id],
        attributes=attributes,
        ext_id=str(user.id),
        update_enabled=True,
    )

    # If user already has a Brevo ID, no need to create a new contact
    if user.brevo_contact_id:
        logger.info(f"Contact {user.email} already exists in Brevo with ID: {user.brevo_contact_id}")
        return

    attempt = 0
    while attempt <= max_retries:
        try:
            api_response = api_instance.create_contact(new_contact).to_dict()
            user.brevo_contact_id = api_response.get("id")
            user.save(update_fields=["brevo_contact_id"])
            logger.info(f"Success Brevo->ContactsApi->create_contact: {user.brevo_contact_id}")
            return
        except ApiException as e:
            # Analyze error type
            error_body = _get_error_body(e)
            # Contact already exists - try to retrieve existing ID
            if e.status == 400 and error_body.get("code") == "duplicate_parameter":
                logger.info(f"Contact {user.id} already exists in Brevo, attempting to retrieve ID...")
                retrieve_and_update_user_brevo_contact_id(user)
                return
            # Rate limiting - wait longer
            should_retry, retry_delay = handle_api_retry(
                e, attempt, max_retries, retry_delay, "creating contact", user.id
            )

            if should_retry:
                logger.info(f"Attempt {attempt+1}/{max_retries+1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                attempt += 1
                continue  # Retry the operation
            else:
                logger.error(f"Failed after {max_retries + 1} attempts for {user.id}")
                raise ContactCreationError(
                    f"Failed to create contact for user {user.id} after {max_retries + 1} attempts", e
                )

    raise ContactCreationError(f"Failed to create contact for user {user.id} after {max_retries + 1} attempts")


def retrieve_and_update_user_brevo_contact_id(user):
    """
    Retrieve and update user's Brevo contact ID by email

    Args:
        user: User object to update

    Raises:
        ContactRetrievalError: When contact retrieval fails
    """
    try:
        # Search for contact by email
        existing_contacts = get_contacts_by_email(user.email)
        if existing_contacts:
            user.brevo_contact_id = existing_contacts.get("id")
            user.save(update_fields=["brevo_contact_id"])
            logger.info(f"Brevo ID retrieved for {user.email}: {user.brevo_contact_id}")
        else:
            raise ContactRetrievalError(f"No contact found for email {user.email}")
    except Exception as lookup_error:
        logger.error(f"Error retrieving contact ID: {lookup_error}")
        raise ContactRetrievalError(f"Error retrieving contact ID for {user.email}", lookup_error)


def get_contacts_by_email(email):
    """
    Retrieves Brevo contacts with a specific email address

    Args:
        email (str): Email address to search for

    Returns:
        dict: Dictionary {email: id} of found contacts
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    try:
        # Search contacts by email
        response = api_instance.get_contact_info(email)
        return response.to_dict()
    except ApiException as e:
        if e.status != 404:  # Ignore 404 errors (contact not found)
            logger.error(f"Error searching for contact by email {email}: {e}")

    return {}


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
        error_body = _get_error_body(e)
        if error_body.get("message") == "Contact already removed from list and/or does not exist":
            logger.info("calling Brevo->ContactsApi->remove_contact_from_list: contact doesn't exist in this list")
        else:
            logger.error(f"Exception when calling Brevo->ContactsApi->remove_contact_from_list: {e}")


def create_or_update_company(siae, max_retries=3, retry_delay=5):
    """
    Create or update a company in Brevo CRM

    Args:
        siae: SIAE (company) object to synchronize with Brevo
        max_retries (int): Maximum number of retry attempts in case of error
        retry_delay (int): Delay in seconds between retry attempts

    Raises:
        CompanySyncError: When company synchronization fails after all retries
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

    sync_log = {
        "date": datetime.now().isoformat(),
        "operation": "update" if siae.brevo_company_id else "create",
    }

    is_update = bool(siae.brevo_company_id)

    for attempt in range(max_retries):
        try:
            if is_update:
                api_instance.companies_id_patch(siae.brevo_company_id, siae_brevo_company_body)
            else:
                api_response = api_instance.companies_post(siae_brevo_company_body)
                siae.brevo_company_id = api_response.id
                sync_log["brevo_company_id"] = siae.brevo_company_id

            # Success
            sync_log["status"] = "success"
            siae.logs.append({"brevo_sync": sync_log})

            if is_update:
                siae.save(update_fields=["logs"])
            else:
                siae.save(update_fields=["brevo_company_id", "logs"])
                # Link contacts after creation
                try:
                    link_company_with_contact_list(
                        siae.brevo_company_id, list(siae.users.values_list("brevo_contact_id", flat=True))
                    )
                except Exception as link_error:
                    logger.warning(f"Error linking company {siae.id} with its contacts: {link_error}")

            return

        except ApiException as e:
            if is_update and e.status == 404:
                logger.warning(
                    f"Company {siae.id} (ID {siae.brevo_company_id}) not found in Brevo, attempting to create..."
                )
                # set the brevo_company_id to None to retry creation
                siae.brevo_company_id = None
                siae.save(update_fields=["brevo_company_id"])
                create_or_update_company(siae, max_retries, retry_delay)
                return

            should_retry, wait_time = handle_api_retry(
                e, attempt, max_retries, retry_delay, f"{'updating' if is_update else 'creating'} company", siae.id
            )

            if should_retry:
                time.sleep(wait_time)
                continue
            else:
                sync_log["status"] = "error"
                sync_log["error"] = str(e)
                siae.logs.append({"brevo_sync": sync_log})
                siae.save(update_fields=["logs"])
                raise CompanySyncError(
                    f"Failed to {'update' if is_update else 'create'} company {siae.id} "
                    f"after {max_retries} attempts",
                    e,
                )

    raise CompanySyncError(
        f"Failed to {'update' if is_update else 'create'} company {siae.id} after {max_retries} attempts"
    )


def create_or_update_buyer_company(company, max_retries=3, retry_delay=5):
    """
    Creates or updates a buyer company in Brevo CRM

    Args:
        company: Company (buyer) object to synchronize with Brevo
        max_retries (int): Maximum number of retry attempts in case of error
        retry_delay (int): Delay in seconds between retry attempts

    Returns:
        bool: True if operation was successful, False otherwise
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)

    company_brevo_body = sib_api_v3_sdk.Body(
        name=company.name,
        attributes={
            # default attributes
            "domain": company.website,
            "phone_number": "",  # Company model doesn't have phone
            # custom attributes
            "app_id": company.id,
            "siae": False,  # This is a buyer company, not SIAE
            "description": company.description,
            "kind": "BUYER",  # Distinguish from SIAE
            "siret": company.siret,
            "app_admin_url": get_object_admin_url(company),
            "nombre_utilisateurs": company.extra_data.get("brevo_company_data", {}).get("user_count"),
            "nombre_besoins": company.extra_data.get("brevo_company_data", {}).get("user_tender_count"),
            "email_domains": ",".join(company.email_domain_list) if company.email_domain_list else "",
        },
    )

    sync_log = {
        "date": datetime.now().isoformat(),
        "operation": "update" if company.brevo_company_id else "create",
    }

    is_update = bool(company.brevo_company_id)

    for attempt in range(max_retries):
        try:
            if is_update:
                api_response = api_instance.companies_id_patch(company.brevo_company_id, company_brevo_body)
            else:
                api_response = api_instance.companies_post(company_brevo_body)
                company.brevo_company_id = api_response.id
                sync_log["brevo_company_id"] = company.brevo_company_id

            # Succès commun
            sync_log["status"] = "success"
            company.logs.append({"brevo_sync": sync_log})

            if is_update:
                company.save(update_fields=["logs"])
            else:
                company.save(update_fields=["brevo_company_id", "logs"])
                # Lier les contacts après création
                try:
                    link_company_with_contact_list(
                        company.brevo_company_id, list(company.users.values_list("brevo_contact_id", flat=True))
                    )
                except Exception as link_error:
                    logger.warning(f"Error linking buyer company {company.id} with its contacts: {link_error}")

            return True

        except ApiException as e:
            if is_update and e.status == 404:
                logger.warning(
                    f"""Buyer company {company.id} (ID {company.brevo_company_id}) not found in Brevo,
                    attempting to create..."""
                )
                # set the brevo_company_id to None to retry creation
                company.brevo_company_id = None
                company.save(update_fields=["brevo_company_id"])
                return create_or_update_buyer_company(company, max_retries, retry_delay)

            should_retry, wait_time = handle_api_retry(
                e,
                attempt,
                max_retries,
                retry_delay,
                f"{'updating' if is_update else 'creating'} buyer company",
                company.id,
            )

            if should_retry:
                time.sleep(wait_time)
                continue
            else:
                sync_log["status"] = "error"
                sync_log["error"] = str(e)
                company.logs.append({"brevo_sync": sync_log})
                company.save(update_fields=["logs"])
                return False

    return False


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


def link_company_with_contact_list(brevo_company_id: int, contact_list: list):
    """
    Links a Brevo company to a list of contacts. If no contact list is provided, it defaults
    to linking the company with the siae's users.

    This function uses the siae's stored company ID and either a provided list of contact IDs or the
    siae author's user(s) ID(s) to link contacts to the company in the Brevo CRM.

    Args:
        brevo_company_id (int): The Brevo company ID to link contacts to.
        contact_list (list of int, optional): List of contact IDs to be linked with the company. Defaults to None.

    Raises:
        ApiException: If an error occurs during the linking process in the Brevo API.
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.CompaniesApi(api_client)

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            # get brevo ids
            brevo_crm_company_id = brevo_company_id

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
    list_id: int = settings.BREVO_CL_SIGNUP_BUYER_ID, limit=500, offset=0, max_retries=3, retry_delay=5
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
            logger.debug(f"Contacts fetched: {len(contacts)} at offset {offset}")
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
