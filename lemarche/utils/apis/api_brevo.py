import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException

from lemarche.tenders.enums import TenderSourcesChoices
from lemarche.utils.apis.brevo_attributes import BUYER_COMPANY_ATTRIBUTES, CONTACT_ATTRIBUTES, SIAE_COMPANY_ATTRIBUTES
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX
from lemarche.utils.data import sanitize_to_send_by_email
from lemarche.utils.urls import get_object_admin_url, get_object_share_url


logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")


@dataclass
class BrevoConfig:
    """Configuration class for Brevo API operations."""

    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5
    rate_limit_backoff_multiplier: int = 2

    # Pagination configuration
    default_page_limit: int = 500
    contacts_default_since_days: int = 30

    @property
    def is_production_env(self) -> bool:
        """Check if we're in production environment."""
        return settings.BITOUBI_ENV not in ENV_NOT_ALLOWED


class BrevoApiError(Exception):
    """Exception raised when contacts fetching fails after all retries"""

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)


class BrevoBaseApiClient:

    api_client: sib_api_v3_sdk.ApiClient

    def __init__(self, config: BrevoConfig = BrevoConfig()):
        """
        Initialize the Brevo API client with configuration.

        Args:
            config (BrevoConfig, optional): Configuration instance. If None, uses default config.
        """
        self.config = config
        self.set_api_client()
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_api_client(self):
        config = sib_api_v3_sdk.Configuration()
        config.api_key["api-key"] = settings.BREVO_API_KEY
        self.api_client = sib_api_v3_sdk.ApiClient(config)

    def handle_api_retry(self, exception: ApiException, attempt, operation_name):
        """
        Helper function to handle API retry logic with exponential backoff

        Args:
            exception: The API exception that occurred
            attempt: Current attempt number (0-based)
            operation_name: Name of the operation for logging

        Returns:
            tuple: (should_retry: bool, wait_time: int)
        """
        max_retries = self.config.max_retries
        retry_delay = self.config.retry_delay

        if exception.status == 429:  # Rate limiting
            wait_time = retry_delay * (attempt + 1) * self.config.rate_limit_backoff_multiplier
            self.logger.warning(f"Rate limit reached while {operation_name}, waiting {wait_time}s")
            return True, wait_time

        # For other errors
        if attempt < max_retries:
            wait_time = retry_delay * (attempt + 1)
            self.logger.warning(
                f"Error {operation_name}, attempt {attempt + 1}/{max_retries} " f"in {wait_time}s: {exception}"
            )
            return True, wait_time
        else:
            self.logger.error(f"Failed after {max_retries} attempts to {operation_name}: {exception}")
            return False, 0

    @classmethod
    def execute_with_retry_method(cls, operation_name="API operation"):
        """
        Class decorator to execute an API operation with retry logic

        Args:
            operation_name: Name of the operation for logging

        Returns:
            Decorator function
        """

        def decorator(operation_func):
            def wrapper(self, *args, **kwargs):
                max_retries = self.config.max_retries

                for attempt in range(max_retries + 1):
                    try:
                        return operation_func(self, *args, **kwargs)
                    except ApiException as e:
                        should_retry, wait_time = self.handle_api_retry(e, attempt, operation_name)

                        if should_retry:
                            self.logger.info(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed, retrying in {wait_time}s..."
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            self.logger.error(f"Failed after {max_retries + 1} attempts for {operation_name}")
                            raise BrevoApiError(f"Failed to {operation_name} after {max_retries + 1} attempts", e)
                    except Exception as e:
                        self.logger.error(f"Unexpected error during {operation_name}: {e}")
                        raise BrevoApiError(f"Unexpected error during {operation_name}: {e}", e)

                raise BrevoApiError(f"Failed to {operation_name} after {max_retries + 1} attempts")

            return wrapper

        return decorator


class BrevoContactsApiClient(BrevoBaseApiClient):
    """
    Client for Brevo Contacts API operations.

    This class provides methods for:
    - Creating and updating contacts
    - Retrieving contacts (individual, bulk, from lists)
    - Managing contact lists and blacklist status
    """

    # =============================================================================
    # CONFIGURATION & INITIALIZATION
    # =============================================================================

    def __init__(self, config: BrevoConfig = BrevoConfig()):
        """
        Initialize the Brevo Contacts API client.

        Args:
            config (BrevoConfig, optional): Configuration instance. If None, uses default config.
        """
        super().__init__(config)
        self.api_instance = sib_api_v3_sdk.ContactsApi(self.api_client)

    # =============================================================================

    # PUBLIC METHODS - CORE CONTACT OPERATIONS
    # =============================================================================

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="creating contact")
    def create_contact(self, user, list_id: int, tender=None):
        """
        Create or update a contact in Brevo

        Args:
            user: User object to send to Brevo
            list_id (int): Brevo list ID to add the contact to
            tender: Tender object associated with the user (optional)

        Returns:
            dict: API response with contact ID if successful

        Raises:
            BrevoApiError: When contact creation fails after all retries
        """

        # If user already has a Brevo ID, no need to create a new contact
        if user.brevo_contact_id:
            self.logger.info(f"Contact {user.email} already exists in Brevo with ID: {user.brevo_contact_id}")
            return {"id": user.brevo_contact_id}

        attributes: dict[str, str | None] = {
            CONTACT_ATTRIBUTES["NOM"]: sanitize_to_send_by_email(user.last_name.capitalize()),
            CONTACT_ATTRIBUTES["PRENOM"]: sanitize_to_send_by_email(user.first_name.capitalize()),
            CONTACT_ATTRIBUTES["DATE_INSCRIPTION"]: user.created_at,
            CONTACT_ATTRIBUTES["TYPE_ORGANISATION"]: user.buyer_kind_detail,
            CONTACT_ATTRIBUTES["NOM_ENTREPRISE"]: sanitize_to_send_by_email(user.company_name.capitalize()),
            CONTACT_ATTRIBUTES["SMS"]: sanitize_to_send_by_email(user.phone_display),
            CONTACT_ATTRIBUTES["MONTANT_BESOIN_ACHETEUR"]: None,
            CONTACT_ATTRIBUTES["TYPE_BESOIN_ACHETEUR"]: None,
            CONTACT_ATTRIBUTES["TYPE_VERTICALE_ACHETEUR"]: None,
        }

        if tender:
            attributes |= self._additional_tender_attributes(tender)

        new_contact = sib_api_v3_sdk.CreateContact(
            email=user.email,
            list_ids=[list_id],
            attributes=attributes,
            ext_id=str(user.id),
            update_enabled=True,
        )

        try:
            api_response = self.api_instance.create_contact(new_contact).to_dict()
            self.logger.info(f"Success Brevo->ContactsApi->create_contact: {api_response.get('id')}")
            return api_response
        except ApiException as e:
            # Analyze error type
            error_body = self._get_error_body(e)
            # Contact already exists - try to retrieve existing ID
            if e.status == 400 and error_body and error_body.get("code") == "duplicate_parameter":
                self.logger.info(f"Contact {user.id} already exists in Brevo, attempting to retrieve ID...")
                self.retrieve_and_update_user_brevo_contact_id(user)
                return {"id": user.brevo_contact_id}
            raise e  # Re-raise for retry logic

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="getting contact by email")
    def get_contact_by_email(self, email: str):
        """
        Retrieves Brevo contact by email address

        Args:
            email (str): Email address to search for

        Returns:
            dict: Contact information if found, empty dict otherwise

        Raises:
            BrevoApiError: When contact retrieval fails after all retries
        """
        try:
            response = self.api_instance.get_contact_info(email)
            return response.to_dict()
        except ApiException as e:
            if e.status == 404:  # Contact not found
                return {}
            raise e  # Re-raise for retry logic

    def get_all_contacts(self, limit_max=None, since_days=None):
        """
        Retrieves all contacts from Brevo, with optional filtering by modification date
        and limiting the total number of contacts returned.

        Args:
            limit_max (int, optional): Maximum number of contacts to retrieve in total.
                If None, retrieves all available contacts. Defaults to None.
            since_days (int, optional): Retrieve only contacts modified in the last X days.
                Uses config default if None.

        Returns:
            dict: Dictionary mapping contact emails to their IDs

        Raises:
            BrevoApiError: When contacts fetching fails after all retries
        """
        # Use configuration defaults
        since_days = since_days or self.config.contacts_default_since_days

        # Initialize local state variables
        offset = 0
        modified_since = datetime.now() - timedelta(days=since_days)
        result = {}
        total_retrieved = 0

        self.logger.debug(f"Retrieving contacts modified in the last {since_days} days")

        try:
            while True:
                # Calculate current limit for this request
                pagination_limit = self._calculate_pagination_limit(
                    limit_max, total_retrieved, self.config.default_page_limit
                )

                if pagination_limit <= 0:
                    break

                self.logger.debug(f"Fetching contacts: limit={pagination_limit}, offset={offset}")

                # Execute the fetch operation with retry logic
                try:
                    contacts, total_count_users = self._fetch_contacts_page(pagination_limit, offset, modified_since)
                except BrevoApiError:
                    self.logger.error("Failed to retrieve contacts page after all retries")
                    break

                self.logger.debug(f"Retrieved {len(contacts)}/{total_count_users} contacts")

                # Process retrieved contacts
                for contact in contacts:
                    result[contact.get("email")] = contact.get("id")
                total_retrieved += len(contacts)

                # Determine if we should continue pagination
                if not self._should_continue_pagination(len(contacts), pagination_limit, total_retrieved, limit_max):
                    break
                else:
                    offset += pagination_limit

        except BrevoApiError:
            # Error occurred and max retries exceeded, return empty result
            self.logger.error("Failed to retrieve contacts after all retries")
            result = {}

        self.logger.debug(f"Total contacts retrieved: {total_retrieved}")
        return result

    def get_contacts_from_list(self, list_id: int, limit=None, offset=0):
        """
        Get all contacts from a specific list with pagination

        Args:
            list_id (int): ID of the list to fetch contacts from
            limit (int): Number of contacts per page (uses config default if None)
            offset (int): Offset for pagination

        Returns:
            dict: Dictionary mapping contact emails to their IDs

        Raises:
            BrevoApiError: When contact retrieval fails after all retries
        """
        # Use configuration defaults
        limit = limit or self.config.default_page_limit

        result = {}
        current_offset = offset
        is_finished = False

        while not is_finished:
            try:
                api_response = self._get_contacts_from_list_with_retry(list_id, limit, current_offset)

                contacts = api_response.get("contacts", [])
                self.logger.debug(f"Contacts fetched: {len(contacts)} at offset {current_offset}")

                for contact in contacts:
                    result[contact.get("email")] = contact.get("id")

                # Check if we should continue pagination
                if len(contacts) < limit:
                    is_finished = True
                else:
                    current_offset += limit

            except BrevoApiError:
                # Error already logged in retry decorator
                break

        return result

    # =============================================================================
    # PUBLIC METHODS - CONTACT UPDATES
    # =============================================================================

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="updating contact")
    def update_contact(self, user_identifier: str, attributes_to_update: dict):
        """
        Update a contact in Brevo

        Args:
            user_identifier (str): Contact identifier (email or ID)
            attributes_to_update (dict): Attributes to update

        Returns:
            dict: API response if successful

        Raises:
            BrevoApiError: When contact update fails after all retries
        """
        update_contact_obj = sib_api_v3_sdk.UpdateContact(attributes=attributes_to_update)
        api_response = self.api_instance.update_contact(identifier=user_identifier, update_contact=update_contact_obj)
        self.logger.info(f"Success Brevo->ContactsApi->update_contact: {api_response}")
        return api_response

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="updating contact email blacklist")
    def update_contact_email_blacklisted(self, user_identifier: str, email_blacklisted: bool):
        """
        Update the email blacklist status of a contact

        Args:
            user_identifier (str): Contact identifier (email or ID)
            email_blacklisted (bool): Whether to blacklist the email

        Returns:
            dict: API response if successful

        Raises:
            BrevoApiError: When contact update fails after all retries
        """
        update_contact_obj = sib_api_v3_sdk.UpdateContact(email_blacklisted=email_blacklisted)
        api_response = self.api_instance.update_contact(identifier=user_identifier, update_contact=update_contact_obj)
        self.logger.info(f"Success Brevo->ContactsApi->update_contact to update email_blacklisted: {api_response}")
        return api_response

    def retrieve_and_update_user_brevo_contact_id(self, user):
        """
        Retrieve and update user's Brevo contact ID by email

        Args:
            user: User object to update

        Raises:
            BrevoApiError: When contact retrieval fails
        """
        try:
            # Search for contact by email
            existing_contact = self.get_contact_by_email(user.email)
            if existing_contact:
                contact_id = existing_contact.get("id")
                if contact_id:
                    user.brevo_contact_id = int(contact_id)
                    user.save(update_fields=["brevo_contact_id"])
                    self.logger.info(f"Brevo ID retrieved for {user.id}: {user.brevo_contact_id}")
                else:
                    raise BrevoApiError(f"No contact ID found for email {user.id}")
            else:
                raise BrevoApiError(f"No contact found for email {user.id}")
        except Exception as lookup_error:
            self.logger.error(f"Error retrieving contact ID: {lookup_error}")
            raise BrevoApiError(f"Error retrieving contact ID for {user.id}", lookup_error)

    # =============================================================================
    # PUBLIC METHODS - LIST MANAGEMENT
    # =============================================================================

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="removing contact from list")
    def remove_contact_from_list(self, user_email: str, list_id: int):
        """
        Remove a contact from a specific list

        Args:
            user_email (str): Email of the contact to remove
            list_id (int): ID of the list to remove contact from

        Returns:
            dict: API response if successful

        Raises:
            BrevoApiError: When contact removal fails after all retries
        """
        contact_emails = sib_api_v3_sdk.RemoveContactFromList(emails=[user_email])
        try:
            api_response = self.api_instance.remove_contact_from_list(list_id=list_id, contact_emails=contact_emails)
            self.logger.info(f"Success Brevo->ContactsApi->remove_contact_from_list: {api_response}")
            return api_response
        except ApiException as e:
            error_body = self._get_error_body(e)
            if error_body and error_body.get("message") == "Contact already removed from list and/or does not exist":
                self.logger.info(
                    "calling Brevo->ContactsApi->remove_contact_from_list: " "contact doesn't exist in this list"
                )
                return {}
            raise e  # Re-raise for retry logic

    # =============================================================================
    # PRIVATE METHODS - UTILITIES
    # =============================================================================

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="fetching contacts page")
    def _fetch_contacts_page(self, limit, offset, modified_since):
        """
        Fetches a single page of contacts from Brevo API

        Args:
            limit: Number of contacts to fetch
            offset: Offset for pagination
            modified_since: Date filter for modifications

        Returns:
            tuple: (list: List of contacts from the API response, int: Total count of contacts)
        """
        api_response = self.api_instance.get_contacts(
            limit=limit, offset=offset, modified_since=modified_since
        ).to_dict()
        return api_response.get("contacts", []), api_response.get("count", 0)

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="getting contacts from list")
    def _get_contacts_from_list_with_retry(self, list_id, limit, offset):
        """Get a page of contacts from a specific list"""
        api_response = self.api_instance.get_contacts_from_list(list_id=list_id, limit=limit, offset=offset).to_dict()
        return api_response

    def _calculate_pagination_limit(self, limit_max, total_retrieved, page_limit):
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

    def _additional_tender_attributes(self, tender):
        """
        Helper function to get additional attributes for a tender when creating a Brevo contact

        Args:
            tender: Tender object to extract attributes from

        Returns:
            dict: Dictionary of additional attributes for the tender
        """
        try:
            first_sector = tender.sectors.first()
            attributes = {
                CONTACT_ATTRIBUTES["MONTANT_BESOIN_ACHETEUR"]: tender.amount_int,
                CONTACT_ATTRIBUTES["TYPE_BESOIN_ACHETEUR"]: tender.kind,
            }

            # Check if there is one sector whose tender source is TALLY
            if tender.source == TenderSourcesChoices.SOURCE_TALLY and first_sector:
                attributes[CONTACT_ATTRIBUTES["TYPE_VERTICALE_ACHETEUR"]] = first_sector.name
            else:
                attributes[CONTACT_ATTRIBUTES["TYPE_VERTICALE_ACHETEUR"]] = None

            return attributes

        except AttributeError as e:
            self.logger.error(f"Attribute error: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

        # Return default values only if an exception occurred
        return {
            CONTACT_ATTRIBUTES["MONTANT_BESOIN_ACHETEUR"]: None,
            CONTACT_ATTRIBUTES["TYPE_BESOIN_ACHETEUR"]: None,
            CONTACT_ATTRIBUTES["TYPE_VERTICALE_ACHETEUR"]: None,
        }

    def _get_error_body(self, exception):
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
            self.logger.error(
                f"Error decoding JSON response: {exception.body if hasattr(exception, 'body') else str(exception)}"
            )
            return {}  # Return empty dict on error

    def _should_continue_pagination(self, contacts_count, pagination_limit, total_retrieved, limit_max):
        """
        Determines if pagination should continue based on various factors.

        Args:
            contacts_count (int): Total number of contacts retrieved so far.
            pagination_limit (int): Limit for the current pagination request.
            total_retrieved (int): Total number of contacts retrieved across all requests.
            limit_max (int): Maximum limit for contacts to retrieve.

        Returns:
            bool: True if pagination should continue, False otherwise.
        """
        if limit_max is not None and total_retrieved >= limit_max:
            return False
        if contacts_count < pagination_limit:
            return False
        return True


class BrevoCompanyApiClient(BrevoBaseApiClient):
    """
    Client for Brevo Companies API operations.

    This class provides methods for:
    - Creating and updating SIAE companies in Brevo CRM
    - Creating and updating buyer companies in Brevo CRM
    - Linking companies with their contacts
    """

    # =============================================================================
    # CONFIGURATION & INITIALIZATION
    # =============================================================================

    def __init__(self, config: BrevoConfig = BrevoConfig()):
        """
        Initialize the Brevo Company API client.

        Args:
            config (BrevoConfig, optional): Configuration instance. If None, uses default config.
        """
        super().__init__(config)
        self.api_instance = sib_api_v3_sdk.CompaniesApi(self.api_client)

    # =============================================================================
    # PUBLIC METHODS - SIAE COMPANY OPERATIONS
    # =============================================================================

    def create_or_update_company(self, siae):
        """
        Create or update a company in Brevo CRM

        Args:
            siae: SIAE (company) object to synchronize with Brevo

        Raises:
            BrevoApiError: When company synchronization fails after all retries
        """
        siae_brevo_company_body = sib_api_v3_sdk.Body(name=siae.name, attributes=self._build_siae_attributes(siae))

        sync_log = self._create_sync_log(siae)
        is_update = bool(siae.brevo_company_id)

        try:
            api_response = self._company_with_retry(siae, siae_brevo_company_body, is_update)
            self._post_process_company_success(siae, api_response, sync_log, is_update)
        except BrevoApiError as e:
            self._handle_company_error(siae, sync_log, e)
            raise e

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="company operation")
    def _company_with_retry(self, siae, siae_brevo_company_body, is_update):
        """Execute the company create or update operation with retry logic"""
        try:
            if is_update:
                return self.api_instance.companies_id_patch(siae.brevo_company_id, siae_brevo_company_body)
            else:
                return self.api_instance.companies_post(siae_brevo_company_body)
        except ApiException as e:
            if is_update and e.status == 404:
                return self._handle_company_404_and_retry(siae, self.create_or_update_buyer_company)
            raise e

    # =============================================================================
    # PUBLIC METHODS - BUYER COMPANY OPERATIONS
    # =============================================================================

    def create_or_update_buyer_company(self, company):
        """
        Creates or updates a buyer company in Brevo CRM

        Args:
            company: Company (buyer) object to synchronize with Brevo

        Returns:
            bool: True if operation was successful, False otherwise
        """

        company_brevo_body = sib_api_v3_sdk.Body(
            name=company.name,
            attributes=self._build_buyer_attributes(company),
        )

        sync_log = self._create_sync_log(company)
        is_update = bool(company.brevo_company_id)

        try:
            api_response = self._buyer_company_with_retry(company, company_brevo_body, is_update)
            self._post_process_company_success(company, api_response, sync_log, is_update)
            return True
        except BrevoApiError as e:
            self._handle_company_error(company, sync_log, e)
            return False

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="buyer company operation")
    def _buyer_company_with_retry(self, company, company_brevo_body, is_update):
        """Execute the buyer company create or update operation with retry logic"""
        try:
            if is_update:
                return self.api_instance.companies_id_patch(company.brevo_company_id, company_brevo_body)
            else:
                return self.api_instance.companies_post(company_brevo_body)
        except ApiException as e:
            if is_update and e.status == 404:
                return self._handle_company_404_and_retry(company, self.create_or_update_buyer_company)
            raise e

    # =============================================================================
    # PUBLIC METHODS - COMPANY-CONTACT LINKING
    # =============================================================================

    def link_company_with_contact_list(self, brevo_company_id: int, contact_list: list):
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
        if self.config.is_production_env:
            try:
                # cleanup
                contact_list = self._cleanup_contact_list(contact_list)
                # link company with contact_list
                if len(contact_list):
                    body_link_company_contact = sib_api_v3_sdk.Body2(link_contact_ids=contact_list)
                    self.api_instance.companies_link_unlink_id_patch(brevo_company_id, body_link_company_contact)
            except ApiException as e:
                self.logger.error(f"Exception when calling Brevo->DealApi->companies_link_unlink_id_patch \n {e}")

    # =============================================================================
    # PRIVATE METHODS - COMMON COMPANY SUPPORT
    # =============================================================================

    def _create_sync_log(self, company):
        """Create a sync log entry for a company operation"""
        return {
            "date": datetime.now().isoformat(),
            "operation": "update" if company.brevo_company_id else "create",
        }

    def _handle_company_error(self, company, sync_log, error):
        """Handle error in company operation by logging and saving"""
        sync_log["status"] = "error"
        sync_log["error"] = str(error)
        company.logs.append({"brevo_sync": sync_log})
        company.save(update_fields=["logs"])

    def _handle_company_404_and_retry(self, company, create_method):
        """Handle 404 error by switching from update to create mode"""
        company_type = "SIAE" if hasattr(company, "kind") and company.kind else "Buyer"
        self.logger.warning(
            f"{company_type} company {company.id} (ID {company.brevo_company_id}) "
            f"not found in Brevo, attempting to create..."
        )
        company.brevo_company_id = None
        company.save(update_fields=["brevo_company_id"])
        return create_method(company)

    def _post_process_company_success(self, company, api_response, sync_log, is_update):
        """Handle post-processing after successful company operation"""
        if not is_update and api_response:
            company.brevo_company_id = api_response.id
            sync_log["brevo_company_id"] = company.brevo_company_id

        sync_log["status"] = "success"
        company.logs.append({"brevo_sync": sync_log})

        if is_update:
            company.save(update_fields=["logs"])
        else:
            company.save(update_fields=["brevo_company_id", "logs"])
            # Link contacts after creation
            try:
                self.link_company_with_contact_list(
                    company.brevo_company_id, list(company.users.values_list("brevo_contact_id", flat=True))
                )
            except Exception as link_error:
                company_type = "SIAE" if hasattr(company, "kind") and company.kind else "buyer"
                self.logger.warning(
                    f"Error linking {company_type} company {company.id} with its contacts: {link_error}"
                )

    def _cleanup_contact_list(self, contact_list):
        """Clean up contact list by removing None values"""
        return [contact_id for contact_id in contact_list if contact_id is not None]

    def _build_buyer_attributes(self, company):
        """
        Build buyer company attributes dictionary for Brevo

        Args:
            company: Company object to extract attributes from

        Returns:
            dict: Dictionary of attributes for Brevo company
        """
        return {
            # Default attributes
            BUYER_COMPANY_ATTRIBUTES["domain"]: company.website,
            BUYER_COMPANY_ATTRIBUTES["phone_number"]: "",  # Company model doesn't have phone
            # Custom attributes
            BUYER_COMPANY_ATTRIBUTES["app_id"]: company.id,
            BUYER_COMPANY_ATTRIBUTES["siae"]: False,  # This is a buyer company, not SIAE
            BUYER_COMPANY_ATTRIBUTES["description"]: company.description,
            BUYER_COMPANY_ATTRIBUTES["kind"]: "BUYER",  # Distinguish from SIAE
            BUYER_COMPANY_ATTRIBUTES["siret"]: company.siret,
            BUYER_COMPANY_ATTRIBUTES["app_admin_url"]: get_object_admin_url(company),
            BUYER_COMPANY_ATTRIBUTES["nombre_d_utilisateurs"]: (
                company.extra_data.get("brevo_company_data", {}).get("user_count")
            ),
            BUYER_COMPANY_ATTRIBUTES["nombre_besoins"]: (
                company.extra_data.get("brevo_company_data", {}).get("user_tender_count")
            ),
            BUYER_COMPANY_ATTRIBUTES["domaines_email"]: (
                ",".join(company.email_domain_list) if company.email_domain_list else ""
            ),
        }

    def _build_siae_attributes(self, siae):
        """
        Build SIAE company attributes dictionary for Brevo

        Args:
            siae: SIAE object to extract attributes from

        Returns:
            dict: Dictionary of attributes for Brevo company
        """
        return {
            # Default attributes
            SIAE_COMPANY_ATTRIBUTES["domain"]: siae.website,
            SIAE_COMPANY_ATTRIBUTES["phone_number"]: siae.contact_phone_display,
            # Custom attributes
            SIAE_COMPANY_ATTRIBUTES["app_id"]: siae.id,
            SIAE_COMPANY_ATTRIBUTES["siae"]: True,
            SIAE_COMPANY_ATTRIBUTES["active"]: siae.is_active,
            SIAE_COMPANY_ATTRIBUTES["description"]: siae.description,
            SIAE_COMPANY_ATTRIBUTES["kind"]: siae.kind,
            SIAE_COMPANY_ATTRIBUTES["address_street"]: siae.address,
            SIAE_COMPANY_ATTRIBUTES["postal_code"]: siae.post_code,
            SIAE_COMPANY_ATTRIBUTES["address_city"]: siae.city,
            SIAE_COMPANY_ATTRIBUTES["contact_email"]: siae.contact_email,
            SIAE_COMPANY_ATTRIBUTES["logo_url"]: siae.logo_url,
            SIAE_COMPANY_ATTRIBUTES["app_url"]: get_object_share_url(siae),
            SIAE_COMPANY_ATTRIBUTES["app_admin_url"]: get_object_admin_url(siae),
            SIAE_COMPANY_ATTRIBUTES["taux_de_completion"]: (
                siae.extra_data.get("brevo_company_data", {}).get("completion_rate")
            ),
            SIAE_COMPANY_ATTRIBUTES["nombre_de_besoins_recus"]: (
                siae.extra_data.get("brevo_company_data", {}).get("tender_received")
            ),
            SIAE_COMPANY_ATTRIBUTES["nombre_de_besoins_interesses"]: (
                siae.extra_data.get("brevo_company_data", {}).get("tender_interest")
            ),
        }


class BrevoTransactionalEmailApiClient(BrevoBaseApiClient):

    def __init__(self, config: BrevoConfig = BrevoConfig()):
        """
        Initialize the Brevo Transactional Email API client.

        Args:
            config (BrevoConfig, optional): Configuration instance. If None, uses default config.
        """
        super().__init__(config)
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(self.api_client)

    @task()
    def send_transactional_email_with_template(
        self,
        template_id: int,
        recipient_email: str,
        recipient_name: str,
        variables: dict,
        subject=None,
        from_email=settings.DEFAULT_FROM_EMAIL,
        from_name=settings.DEFAULT_FROM_NAME,
    ):
        """
        Send a transactional email using a Brevo template

        Args:
            template_id (int): The Brevo template ID
            recipient_email (str): Email address of the recipient
            recipient_name (str): Name of the recipient
            variables (dict): Variables to substitute in the template
            subject (str, optional): Custom subject line
            from_email (str): Sender email address
            from_name (str): Sender name

        Returns:
            dict: API response if successful

        Raises:
            BrevoApiError: When email sending fails after all retries
        """

        if not self.config.is_production_env:
            self.logger.info("Brevo: email not sent (DEV or TEST environment detected)")
            return {"message": "Email not sent in development/test environment"}

        data = {
            "sender": {"email": from_email, "name": from_name},
            "to": [{"email": recipient_email, "name": recipient_name}],
            "template_id": template_id,
            "params": variables,
        }
        # if subject empty, defaults to Brevo's template subject
        if subject:
            data["subject"] = EMAIL_SUBJECT_PREFIX + subject

        return self._send_email_with_retry(data)

    @BrevoBaseApiClient.execute_with_retry_method(operation_name="sending transactional email")
    def _send_email_with_retry(self, data):
        """Execute the send email operation with retry logic"""
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(**data)
        response = self.api_instance.send_transac_email(send_smtp_email)
        self.logger.info("Brevo: send transactional email with template")
        return response.to_dict()


def _cleanup_and_link_contacts(api_instance, entity_id, contact_list: list, link_body_class, patch_method_name):
    """
    Common utility to clean up contact list and execute linking API call

    Args:
        api_instance: Brevo API instance (DealsApi or CompaniesApi)
        entity_id: ID of the entity (deal or company) to link contacts to
        contact_list: List of contact IDs (may contain None values)
        link_body_class: The Brevo SDK body class to use (Body2, Body5, etc.)
        patch_method_name: Name of the API method to call
    """

    # link entity with contact_list
    if len(contact_list):
        body_link = link_body_class(link_contact_ids=contact_list)
        patch_method = getattr(api_instance, patch_method_name)
        patch_method(entity_id, body_link)


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
    c = BrevoBaseApiClient()
    api_instance = sib_api_v3_sdk.DealsApi(c.api_client)
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
    brevo_client = BrevoBaseApiClient()
    api_instance = sib_api_v3_sdk.DealsApi(brevo_client.api_client)

    if brevo_client.config.is_production_env:
        try:
            # get brevo ids
            brevo_crm_deal_id = tender.brevo_deal_id
            # Default to the author's contact ID if no contact list is provided
            if not contact_list:
                contact_list = [tender.author.brevo_contact_id]

            # Use common utility for linking

            _cleanup_and_link_contacts(
                api_instance, brevo_crm_deal_id, contact_list, sib_api_v3_sdk.Body5, "crm_deals_link_unlink_id_patch"
            )

        except ApiException as e:
            logger.error("Exception when calling Brevo->DealApi->crm_deals_link_unlink_id_patch: %s\n" % e)
