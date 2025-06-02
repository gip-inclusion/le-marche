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


def handle_api_retry(exception, attempt, max_retries, retry_delay, operation_name, entity_id):
    """
    Helper function to handle API retry logic with exponential backoff

    Args:
        exception: The API exception that occurred
        attempt: Current attempt number (0-based)
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay in seconds between attempts
        operation_name: Name of the operation for logging
        entity_id: ID of the entity being processed

    Returns:
        tuple: (should_retry: bool, wait_time: int)
    """
    if exception.status == 429:  # Rate limiting
        wait_time = retry_delay * (attempt + 1) * 2
        logger.warning(f"Rate limit reached while {operation_name} {entity_id}, waiting {wait_time}s")
        return True, wait_time

    # For other errors
    if attempt < max_retries - 1:
        wait_time = retry_delay * (attempt + 1)
        logger.warning(
            f"Error {operation_name} {entity_id}, attempt {attempt+1}/{max_retries} in {wait_time}s: {exception}"
        )
        return True, wait_time
    else:
        logger.error(f"Failed after {max_retries} attempts to {operation_name} {entity_id}: {exception}")
        return False, 0


def get_config():
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY
    return config


def get_api_client():
    config = get_config()
    return sib_api_v3_sdk.ApiClient(config)


def get_all_contacts(limit_max=None, since_days=30, verbose=False, max_retries=3):
    """
    Retrieves all contacts from Brevo, with optional filtering by modification date
    and limiting the total number of contacts returned.

    Args:
        limit_max (int, optional): Maximum number of contacts to retrieve in total.
            If None, retrieves all available contacts. Defaults to None.
        since_days (int, optional): Retrieve only contacts modified in the last X days.
            Defaults to 30.
        verbose (bool, optional): Whether to log detailed information. Defaults to False.
        max_retries (int, optional): Maximum number of retry attempts in case of API errors.
            Defaults to 3.

    Returns:
        dict: Dictionary mapping contact emails to their IDs
    """
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.ContactsApi(api_client)

    # Configuration for pagination
    page_limit = 50  # Number of contacts per API request
    offset = 0
    modified_since = datetime.now() - timedelta(days=since_days)

    # Result container
    result = {}
    total_retrieved = 0
    is_finished = False
    retry_count = 0

    if verbose:
        logger.info(f"Retrieving contacts modified in the last {since_days} days")

    while not is_finished:
        try:
            # Apply limit_max if specified to avoid unnecessary API calls
            if limit_max is not None and total_retrieved + page_limit > limit_max:
                current_limit = limit_max - total_retrieved
            else:
                current_limit = page_limit

            if current_limit <= 0:
                break

            if verbose:
                logger.info(f"Fetching contacts: limit={current_limit}, offset={offset}")

            api_response = api_instance.get_contacts(
                limit=current_limit, offset=offset, modified_since=modified_since
            ).to_dict()

            contacts = api_response.get("contacts", [])

            if verbose:
                logger.info(f"Retrieved {len(contacts)} contacts")

            # Process retrieved contacts
            for contact in contacts:
                result[contact.get("email")] = contact.get("id")

            total_retrieved += len(contacts)

            # Determine if we should continue pagination
            if len(contacts) < current_limit:
                # No more contacts to retrieve
                is_finished = True
            elif limit_max is not None and total_retrieved >= limit_max:
                # Reached the maximum limit
                is_finished = True
            else:
                # Continue to next page
                offset += current_limit

            # Reset retry counter on successful request
            retry_count = 0

        except ApiException as e:
            logger.error(f"Exception when calling ContactsApi->get_contacts: {e}")
            retry_count += 1

            if retry_count > max_retries:
                logger.error("Max retries exceeded when fetching contacts. Returning partial results.")
                break

            # Exponential backoff
            wait_time = 2**retry_count
            if verbose:
                logger.warning(f"API error, retrying in {wait_time}s (attempt {retry_count}/{max_retries})")

            time.sleep(wait_time)

        except Exception as e:
            logger.error(f"Unexpected error retrieving contacts: {e}")
            break

    if verbose:
        logger.info(f"Total contacts retrieved: {total_retrieved}")

    return result


def create_contact(user, list_id: int, tender=None, max_retries=3, retry_delay=5):
    """
    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CreateContact.md
    - API: https://developers.brevo.com/reference/createcontact

    Args:
        user: User object to send to Brevo
        list_id (int): Brevo list ID to add the contact to
        tender: Tender object associated with the user (optional)
        max_retries (int): Maximum number of retry attempts in case of error
        retry_delay (int): Delay in seconds between retry attempts

    Returns:
        bool: True if contact was successfully created/updated, False otherwise
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
            if tender.source == TenderSourcesChoices.SOURCE_TALLY and first_sector:
                attributes["TYPE_VERTICALE_ACHETEUR"] = first_sector.name
            else:
                attributes["TYPE_VERTICALE_ACHETEUR"] = None

        except AttributeError as e:
            logger.error(f"Attribute error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

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
        return True

    # Try to create the contact with retry mechanism
    for attempt in range(max_retries):
        try:
            api_response = api_instance.create_contact(new_contact).to_dict()
            user.brevo_contact_id = api_response.get("id")
            user.save(update_fields=["brevo_contact_id"])
            logger.info(f"Success Brevo->ContactsApi->create_contact: {user.brevo_contact_id}")
            return True
        except ApiException as e:
            # Analyze error type
            error_body = {}
            try:
                error_body = json.loads(e.body)
            except (json.JSONDecodeError, AttributeError):
                logger.error(f"Error decoding JSON response: {e.body if hasattr(e, 'body') else str(e)}")
                pass

            # Contact already exists - try to retrieve existing ID
            if e.status == 400 and error_body.get("code") == "duplicate_parameter":
                logger.info(f"Contact {user.id} already exists in Brevo, attempting to retrieve ID...")
                try:
                    # Search for contact by email
                    existing_contacts = get_contacts_by_email(user.email)
                    if existing_contacts:
                        user.brevo_contact_id = existing_contacts.get("id")
                        user.save(update_fields=["brevo_contact_id"])
                        logger.info(f"Brevo ID retrieved for {user.email}: {user.brevo_contact_id}")
                        return True
                except Exception as lookup_error:
                    logger.error(f"Error retrieving contact ID: {lookup_error}")

            # Rate limiting - wait longer
            should_retry, wait_time = handle_api_retry(
                e, attempt, max_retries, retry_delay, "creating contact", user.id
            )

            if should_retry:
                logger.info(f"Attempt {attempt+1}/{max_retries} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue  # Retry the operation
            else:
                logger.error(f"Failed after {max_retries} attempts for {user.id}")
                return False

    return False


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
        error_body = json.loads(e.body)
        if error_body.get("message") == "Contact already removed from list and/or does not exist":
            logger.info("calling Brevo->ContactsApi->remove_contact_from_list: contact doesn't exist in this list")
        else:
            logger.error(f"Exception when calling Brevo->ContactsApi->remove_contact_from_list: {e}")


def create_or_update_company(siae, max_retries=3, retry_delay=5):
    """
    Creates or updates a company in Brevo CRM

    Brevo docs
    - Python library: https://github.com/sendinblue/APIv3-python-library/blob/master/docs/CompaniesApi.md
    - API: https://developers.brevo.com/reference/post_companies

    Args:
        siae: SIAE (company) object to synchronize with Brevo
        max_retries (int): Maximum number of retry attempts in case of error
        retry_delay (int): Delay in seconds between retry attempts

    Returns:
        bool: True if operation was successful, False otherwise
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

    if siae.brevo_company_id:  # update
        for attempt in range(max_retries):
            try:
                api_response = api_instance.companies_id_patch(siae.brevo_company_id, siae_brevo_company_body)
                siae.logs.append({"brevo_sync": sync_log})
                siae.save(update_fields=["logs"])
                return True
            except ApiException as e:
                # If ID no longer exists in Brevo, try to create the company instead
                if e.status == 404:
                    logger.warning(
                        f"Company {siae.id} (ID {siae.brevo_company_id}) not found in Brevo, attempting to create..."
                    )
                    siae.brevo_company_id = None
                    siae.save(update_fields=["brevo_company_id"])
                    return create_or_update_company(siae, max_retries, retry_delay)

                # In case of rate limiting, wait longer
                should_retry, wait_time = handle_api_retry(
                    e, attempt, max_retries, retry_delay, "updating company", siae.id
                )
                if should_retry:
                    time.sleep(wait_time)
                    continue

                # Handle retry logic for other errors
                should_retry, wait_time = handle_api_retry(
                    e, attempt, max_retries, retry_delay, "updating company", siae.id
                )

                if should_retry:
                    time.sleep(wait_time)
                else:
                    sync_log["status"] = "error"
                    sync_log["error"] = str(e)
                    siae.logs.append({"brevo_sync": sync_log})
                    siae.save(update_fields=["logs"])
                    return False
    else:  # create
        for attempt in range(max_retries):
            try:
                api_response = api_instance.companies_post(siae_brevo_company_body)
                siae.brevo_company_id = api_response.id
                sync_log["status"] = "success"
                sync_log["brevo_company_id"] = siae.brevo_company_id
                siae.logs.append({"brevo_sync": sync_log})
                siae.save(update_fields=["brevo_company_id", "logs"])

                # After creating the company, we can try to link the contacts
                try:
                    link_company_with_contact_list(siae)
                except Exception as link_error:
                    logger.warning(f"Error linking company {siae.id} with its contacts: {link_error}")

                return True
            except ApiException as e:
                # Check if company already exists
                if e.status == 400:
                    try:
                        error_body = json.loads(e.body)
                        if error_body.get("code") == "duplicate_parameter":
                            logger.info(f"Company {siae.name} already exists in Brevo, cannot create it again")
                            # We could try to find the existing company by name
                            sync_log["status"] = "warning"
                            sync_log["message"] = "Company exists in Brevo but unable to retrieve ID"
                            siae.logs.append({"brevo_sync": sync_log})
                            siae.save(update_fields=["logs"])
                            return False
                    except (json.JSONDecodeError, AttributeError):
                        pass

                # Rate limiting
                should_retry, wait_time = handle_api_retry(
                    e, attempt, max_retries, retry_delay, "creating company", siae.id
                )
                if should_retry:
                    time.sleep(wait_time)
                    continue

                # Handle retry logic for other errors
                should_retry, wait_time = handle_api_retry(
                    e, attempt, max_retries, retry_delay, "creating company", siae.id
                )

                if should_retry:
                    time.sleep(wait_time)
                else:
                    sync_log["status"] = "error"
                    sync_log["error"] = str(e)
                    siae.logs.append({"brevo_sync": sync_log})
                    siae.save(update_fields=["logs"])
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
