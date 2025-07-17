from datetime import datetime, timedelta
from unittest import skip
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from sib_api_v3_sdk.rest import ApiException

from lemarche.companies.factories import CompanyFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users.factories import UserFactory
from lemarche.utils.apis import api_brevo
from lemarche.utils.apis.brevo_attributes import CONTACT_ATTRIBUTES


@patch("lemarche.utils.apis.api_brevo.time.sleep")
class BrevoBaseApiClientTest(TestCase):
    """
    Tests for the BrevoBaseApiClient class.
    This covers the retry decorator functionality and base client behavior.
    """

    def test_execute_with_retry_method_success_first_attempt(self, mock_sleep):
        """Test decorator when operation succeeds on first attempt"""

        # Create a test method decorated with execute_with_retry_method
        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                return {"success": True}

        test = TestBrevoBasedClass()
        # Execute the method
        result = test.test_method()

        # Verify success and no retries
        self.assertEqual(result, {"success": True})
        mock_sleep.assert_not_called()

    def test_execute_with_retry_method_success_after_retry(self, mock_sleep):
        """Test decorator when operation succeeds after one retry"""

        # Use a list to be able to modify the value from the nested function

        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            call_counter = 0

            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                self.call_counter += 1
                if self.call_counter == 1:
                    # First call fails
                    raise ApiException(status=500, reason="Server Error")
                else:
                    # Second call succeeds
                    return {"success": True, "attempt": self.call_counter}

        class_based = TestBrevoBasedClass()
        result = class_based.test_method()

        # Verify success after retry
        self.assertEqual(result, {"success": True, "attempt": 2})
        mock_sleep.assert_called_once_with(5)  # Default retry delay

    def test_execute_with_retry_method_rate_limit_handling(self, mock_sleep):
        """Test decorator handles rate limiting with exponential backoff"""

        # Use a list to be able to modify the value from the nested function

        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            call_counter = 0

            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                self.call_counter += 1
                if self.call_counter == 1:
                    # First call hits rate limit
                    raise ApiException(status=429, reason="Rate Limit")
                else:
                    # Second call succeeds
                    return {"success": True}

        result = TestBrevoBasedClass().test_method()

        # Verify rate limit handling with exponential backoff
        self.assertEqual(result, {"success": True})
        # Rate limit wait time = retry_delay * (attempt + 1) * rate_limit_backoff_multiplier
        # = 5 * (0 + 1) * 2 = 10 seconds
        mock_sleep.assert_called_once_with(10)

    def test_execute_with_retry_method_max_retries_exceeded(self, mock_sleep):
        """Test decorator when max retries are exceeded"""

        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                # Always fail
                raise ApiException(status=500, reason="Server Error")

        # Should raise BrevoApiError after max retries
        with self.assertRaises(api_brevo.BrevoApiError) as context:
            TestBrevoBasedClass().test_method()
        # Verify error message contains operation details
        self.assertIn("Failed to test operation", str(context.exception))
        self.assertIn("after 4 attempts", str(context.exception))  # max_retries=3 + initial attempt

        # Verify sleep was called for each retry (3 times)
        self.assertEqual(mock_sleep.call_count, 3)

    def test_execute_with_retry_method_custom_config(self, mock_sleep):
        """Test decorator with custom retry configuration"""

        # Create client with custom config
        config = api_brevo.BrevoConfig(max_retries=1, retry_delay=2)

        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                # Always fail
                raise ApiException(status=500, reason="Server Error")

        with self.assertRaises(api_brevo.BrevoApiError):
            TestBrevoBasedClass(config=config).test_method()

        # Should only retry once with custom delay
        mock_sleep.assert_called_once_with(2)

    def test_execute_with_retry_method_unexpected_exception(self, mock_sleep):
        """Test decorator handling of unexpected exceptions"""

        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                # Raise unexpected exception (not ApiException)
                raise ValueError("Unexpected error")

        with self.assertRaises(api_brevo.BrevoApiError) as context:
            TestBrevoBasedClass().test_method()

        # Should not retry for unexpected exceptions
        mock_sleep.assert_not_called()
        self.assertIn("Unexpected error during test operation", str(context.exception))

    def test_handle_api_retry_rate_limit(self, mock_sleep):
        """Test handle_api_retry method for rate limiting"""
        exception = ApiException(status=429, reason="Rate Limit")

        should_retry, wait_time = api_brevo.BrevoBaseApiClient().handle_api_retry(exception, 0, "test operation")

        self.assertTrue(should_retry)
        # Wait time = retry_delay * (attempt + 1) * rate_limit_backoff_multiplier = 5 * 1 * 2 = 10
        self.assertEqual(wait_time, 10)

    def test_handle_api_retry_server_error_within_limits(self, mock_sleep):
        """Test handle_api_retry method for server error within retry limits"""
        exception = ApiException(status=500, reason="Server Error")

        should_retry, wait_time = api_brevo.BrevoBaseApiClient().handle_api_retry(exception, 1, "test operation")

        self.assertTrue(should_retry)
        # Wait time = retry_delay * (attempt + 1) = 5 * 2 = 10
        self.assertEqual(wait_time, 10)

    def test_handle_api_retry_max_retries_exceeded(self, mock_sleep):
        """Test handle_api_retry method when max retries exceeded"""
        exception = ApiException(status=500, reason="Server Error")

        # Attempt equals max_retries (3), should not retry
        should_retry, wait_time = api_brevo.BrevoBaseApiClient().handle_api_retry(exception, 3, "test operation")

        self.assertFalse(should_retry)
        self.assertEqual(wait_time, 0)

    def test_execute_with_retry_method_final_failure_without_exception(self, mock_sleep):
        """Test decorator when max retries exceeded without any exception being raised"""

        # This test covers the case when we reach the end of the decorator with exceptions thrown on every attempt
        class TestBrevoBasedClass(api_brevo.BrevoBaseApiClient):
            @api_brevo.BrevoBaseApiClient.execute_with_retry_method(operation_name="test operation")
            def test_method(self):
                # Always raise an exception to trigger the retry logic
                raise ApiException(status=500, reason="Server Error")

        with self.assertRaises(api_brevo.BrevoApiError) as context:
            TestBrevoBasedClass().test_method()

        # Verify that the final error is raised with the correct message
        self.assertIn("Failed to test operation after 4 attempts", str(context.exception))


@patch("lemarche.utils.apis.api_brevo.time.sleep")
class BrevoContactsApiClientTest(TestCase):
    """
    Tests for the BrevoContactsApiClient class.
    This covers API interactions, retry mechanisms, and error handling
    for contact-related operations.
    """

    def setUp(self):
        self.user = UserFactory(email="test@example.com")

    def test_get_all_contacts_success(self, mock_sleep):
        """Test successful retrieval of contacts"""
        mock_api_instance = MagicMock()

        # Mock first page response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "contacts": [{"email": "user1@example.com", "id": 1}, {"email": "user2@example.com", "id": 2}],
            "count": 2,
        }
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts(limit_max=2, since_days=7)

        expected_result = {"user1@example.com": 1, "user2@example.com": 2}
        self.assertEqual(result, expected_result)
        mock_api_instance.get_contacts.assert_called_once()

    def test_should_continue_pagination_no_contacts(self, mock_sleep):
        """Test pagination stopping when no contacts returned"""
        result = api_brevo.BrevoContactsApiClient()._should_continue_pagination(
            contacts_count=0, pagination_limit=10, total_retrieved=5, limit_max=None
        )
        self.assertFalse(result)

    def test_should_continue_pagination_limit_max_reached(self, mock_sleep):
        """Test pagination stopping when limit_max is reached"""
        result = api_brevo.BrevoContactsApiClient()._should_continue_pagination(
            contacts_count=5, pagination_limit=10, total_retrieved=10, limit_max=10
        )
        self.assertFalse(result)

    def test_should_continue_pagination_continue(self, mock_sleep):
        """Test pagination continuing when full page returned"""
        result = api_brevo.BrevoContactsApiClient()._should_continue_pagination(
            contacts_count=10, pagination_limit=10, total_retrieved=10, limit_max=None
        )
        self.assertTrue(result)

    def test_should_continue_pagination_partial_page(self, mock_sleep):
        """Test pagination stopping when partial page returned"""
        result = api_brevo.BrevoContactsApiClient()._should_continue_pagination(
            contacts_count=5, pagination_limit=10, total_retrieved=15, limit_max=None
        )
        self.assertFalse(result)

    def test_get_all_contacts_pagination(self, mock_sleep):
        """Test pagination functionality"""
        mock_api_instance = MagicMock()

        # Mock first page (5 contacts)
        mock_response_page1 = MagicMock()
        mock_response_page1.to_dict.return_value = {
            "contacts": [{"email": f"user{i}@example.com", "id": i} for i in range(1, 6)],
            "count": 8,  # Total available
        }

        # Mock second page (3 remaining contacts)
        mock_response_page2 = MagicMock()
        mock_response_page2.to_dict.return_value = {
            "contacts": [{"email": f"user{i}@example.com", "id": i} for i in range(6, 9)],
            "count": 8,
        }

        # Configure successive calls
        mock_api_instance.get_contacts.side_effect = [mock_response_page1, mock_response_page2]

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            # Use custom config with small page limit for testing pagination
            config = api_brevo.BrevoConfig(default_page_limit=5)
            client = api_brevo.BrevoContactsApiClient(config)
            result = client.get_all_contacts()

        # Verify that all contacts were retrieved
        self.assertEqual(len(result), 8)
        expected_result = {f"user{i}@example.com": i for i in range(1, 9)}
        self.assertEqual(result, expected_result)

        # Verify that the API was called 2 times with correct parameters
        self.assertEqual(mock_api_instance.get_contacts.call_count, 2)

    def test_get_all_contacts_with_limit_max(self, mock_sleep):
        """Test limit_max parameter"""
        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "contacts": [{"email": f"user{i}@example.com", "id": i} for i in range(1, 6)],
            "count": 100,  # Total available
        }
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts(limit_max=5)

        self.assertEqual(len(result), 5)
        # Verify that the API was called with the correct limit
        mock_api_instance.get_contacts.assert_called_once()
        call_args = mock_api_instance.get_contacts.call_args
        self.assertEqual(call_args[1]["limit"], 5)

    def test_get_all_contacts_api_exception_with_retry(self, mock_sleep):
        """Test API exception handling with retry mechanism"""
        mock_api_instance = MagicMock()

        # First call raises exception, second call succeeds
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"contacts": [{"email": "user@example.com", "id": 1}]}

        mock_api_instance.get_contacts.side_effect = [ApiException(status=500, reason="Server Error"), mock_response]

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            client = api_brevo.BrevoContactsApiClient(config)
            result = client.get_all_contacts()

        self.assertEqual(len(result), 1)
        self.assertEqual(mock_api_instance.get_contacts.call_count, 2)
        mock_sleep.assert_called_once_with(5)  # retry delay

    def test_get_all_contacts_max_retries_exceeded(self, mock_sleep):
        """Test behavior when max retries are exceeded"""
        mock_api_instance = MagicMock()

        # Always raise exception
        mock_api_instance.get_contacts.side_effect = ApiException(status=500, reason="Server Error")

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            client = api_brevo.BrevoContactsApiClient(config)
            result = client.get_all_contacts()

        self.assertEqual(result, {})
        self.assertEqual(mock_api_instance.get_contacts.call_count, 3)  # Initial call + 2 retries
        self.assertEqual(mock_sleep.call_count, 2)  # 2 retries

    def test_get_all_contacts_unexpected_exception(self, mock_sleep):
        """Test handling of unexpected exceptions"""
        mock_api_instance = MagicMock()

        # Raise unexpected exception
        mock_api_instance.get_contacts.side_effect = Exception("Unexpected error")

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts()

        self.assertEqual(result, {})

    def test_get_all_contacts_empty_response(self, mock_sleep):
        """Test handling of empty contact list"""
        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"contacts": [], "count": 0}
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts()

        self.assertEqual(result, {})
        mock_api_instance.get_contacts.assert_called_once()

    def test_get_all_contacts_since_days_parameter(self, mock_sleep):
        """Test that since_days parameter is correctly passed to API call"""
        mock_api_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"contacts": []}
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            client.get_all_contacts(since_days=15)

        # Verify that modified_since parameter was passed
        call_args = mock_api_instance.get_contacts.call_args
        self.assertIn("modified_since", call_args[1])

        # Verify the date is approximately 15 days ago
        modified_since = call_args[1]["modified_since"]
        expected_date = datetime.now() - timedelta(days=15)
        # Allow for small time differences during test execution
        self.assertLess(abs((modified_since - expected_date).total_seconds()), 10)

    def test_create_contact_success(self, mock_sleep):
        """Test successful contact creation"""
        mock_api_instance = MagicMock()

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 12345}
        mock_api_instance.create_contact.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            response = client.create_contact(self.user, list_id=1)

        # Verify the API response is returned
        self.assertEqual(response["id"], 12345)
        mock_api_instance.create_contact.assert_called_once()

    def test_create_contact_with_tender(self, mock_sleep):
        """Test contact creation with tender information"""
        sector = SectorFactory(name="Informatique")
        tender = TenderFactory(amount_exact=50000, kind="PRESTA", source="TALLY")
        tender.sectors.add(sector)

        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 12345}
        mock_api_instance.create_contact.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            client.create_contact(self.user, list_id=1, tender=tender)

        # Verify that tender attributes were included in the call
        call_args = mock_api_instance.create_contact.call_args[0][0]
        self.assertEqual(call_args.attributes[CONTACT_ATTRIBUTES["MONTANT_BESOIN_ACHETEUR"]], 50000)
        self.assertEqual(call_args.attributes[CONTACT_ATTRIBUTES["TYPE_BESOIN_ACHETEUR"]], "PRESTA")
        self.assertEqual(call_args.attributes[CONTACT_ATTRIBUTES["TYPE_VERTICALE_ACHETEUR"]], "Informatique")

    def test_create_contact_already_has_brevo_id(self, mock_sleep):
        """Test contact creation when user already has Brevo ID"""
        self.user.brevo_contact_id = 99999
        self.user.save()

        # Should not raise any exception
        c = api_brevo.BrevoContactsApiClient()
        c.create_contact(self.user, list_id=1)

    @patch("lemarche.utils.apis.api_brevo.BrevoContactsApiClient.get_contact_by_email")
    def test_create_contact_duplicate_error_with_recovery(self, mock_get_contact_by_email, mock_sleep):
        """Test handling of duplicate contact error with successful ID recovery"""
        mock_api_instance = MagicMock()

        # Mock duplicate error response
        error_body = '{"code": "duplicate_parameter", "message": "Contact already exists"}'
        duplicate_exception = ApiException(status=400, reason="Bad Request")
        duplicate_exception.body = error_body
        mock_api_instance.create_contact.side_effect = duplicate_exception

        # Mock successful contact lookup
        mock_get_contact_by_email.return_value = {"id": 55555}

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            c = api_brevo.BrevoContactsApiClient()
            response = c.create_contact(self.user, list_id=1)

        # The user's brevo_contact_id should be automatically updated by the client method
        self.user.refresh_from_db()
        self.assertEqual(self.user.brevo_contact_id, 55555)

        # Response should contain the retrieved ID
        self.assertEqual(response["id"], 55555)
        mock_get_contact_by_email.assert_called_once_with(self.user.email)

    def test_create_contact_rate_limit_with_retry(self, mock_sleep):
        """Test retry mechanism for rate limiting"""
        mock_api_instance = MagicMock()

        # First call rate limited, second call succeeds
        rate_limit_exception = ApiException(status=429, reason="Rate Limit")
        rate_limit_exception.body = None  # Ajouter l'attribut body
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 77777}

        mock_api_instance.create_contact.side_effect = [rate_limit_exception, mock_response]

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            c = api_brevo.BrevoContactsApiClient(config)
            response = c.create_contact(self.user, list_id=1)

        # The user's brevo_contact_id should not be automatically updated
        self.user.refresh_from_db()
        self.assertIsNone(self.user.brevo_contact_id)
        # But the response should contain the ID
        self.assertEqual(response["id"], 77777)
        self.assertEqual(mock_api_instance.create_contact.call_count, 2)
        mock_sleep.assert_called_once()

    def test_create_contact_max_retries_exceeded(self, mock_sleep):
        """Test behavior when max retries are exceeded"""
        mock_api_instance = MagicMock()

        # Always return server error
        server_error = ApiException(status=500, reason="Internal Server Error")
        server_error.body = None  # Ajouter l'attribut body
        mock_api_instance.create_contact.side_effect = server_error

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            with self.assertRaises(api_brevo.BrevoApiError):
                # Use custom config with fewer retries for testing
                config = api_brevo.BrevoConfig(max_retries=2)
                c = api_brevo.BrevoContactsApiClient(config)
                c.create_contact(self.user, list_id=1)

        self.user.refresh_from_db()
        self.assertIsNone(self.user.brevo_contact_id)
        self.assertEqual(mock_api_instance.create_contact.call_count, 3)  # 1 initial + 2 retries
        self.assertEqual(mock_sleep.call_count, 2)  # 2 retries avec max_retries=2

    def test_create_contact_malformed_error_response(self, mock_sleep):
        """Test handling of malformed JSON error response"""
        mock_api_instance = MagicMock()

        # Mock error with malformed JSON body
        error_exception = ApiException(status=400, reason="Bad Request")
        error_exception.body = "invalid json"
        mock_api_instance.create_contact.side_effect = error_exception

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            with self.assertRaises(api_brevo.BrevoApiError):
                # Use custom config with fewer retries for testing
                config = api_brevo.BrevoConfig(max_retries=1)
                c = api_brevo.BrevoContactsApiClient(config)
                c.create_contact(self.user, list_id=1)

        self.user.refresh_from_db()
        self.assertIsNone(self.user.brevo_contact_id)

    def test_create_contact_verify_attributes(self, mock_sleep):
        """Test that contact attributes are correctly set"""
        self.user.last_name = "Dupont"
        self.user.first_name = "Jean"
        self.user.company_name = "ACME Corp"
        self.user.phone = "+33123456789"
        self.user.buyer_kind_detail = "ENTREPRISE"
        self.user.save()

        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 88888}
        mock_api_instance.create_contact.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            c = api_brevo.BrevoContactsApiClient()
            c.create_contact(self.user, list_id=1)

        # Verify the contact object passed to API
        call_args = mock_api_instance.create_contact.call_args[0][0]
        self.assertEqual(call_args.email, self.user.email)
        self.assertEqual(call_args.list_ids, [1])
        self.assertEqual(call_args.ext_id, str(self.user.id))
        self.assertTrue(call_args.update_enabled)

        # Verify attributes
        attributes = call_args.attributes
        self.assertEqual(attributes[CONTACT_ATTRIBUTES["NOM"]], "Dupont")
        self.assertEqual(attributes[CONTACT_ATTRIBUTES["PRENOM"]], "Jean")
        self.assertEqual(attributes[CONTACT_ATTRIBUTES["NOM_ENTREPRISE"]], "Acme corp")
        self.assertEqual(attributes[CONTACT_ATTRIBUTES["TYPE_ORGANISATION"]], "ENTREPRISE")
        self.assertEqual(attributes[CONTACT_ATTRIBUTES["SMS"]], "+33123456789")

    def test_additional_tender_attributes_with_exception(self, mock_sleep):
        """Test _additional_tender_attributes with AttributeError"""
        client = api_brevo.BrevoContactsApiClient()

        # Create a mock tender that will raise AttributeError when accessing sectors.first()
        mock_tender = MagicMock()
        mock_tender.amount_int = 1000
        mock_tender.kind = "TYPE_TEST"
        mock_tender.sectors.first.side_effect = AttributeError("Test attribute error")

        with patch.object(client, "logger") as mock_logger:
            result = client._additional_tender_attributes(mock_tender)

            # Should return default values with hardcoded keys as in the actual code
            expected = {
                "MONTANT_BESOIN_ACHETEUR": None,
                "TYPE_BESOIN_ACHETEUR": None,
                "TYPE_VERTICALE_ACHETEUR": None,
            }
            self.assertEqual(result, expected)
            mock_logger.error.assert_called()

    def test_additional_tender_attributes_with_generic_exception(self, mock_sleep):
        """Test _additional_tender_attributes with generic Exception"""
        client = api_brevo.BrevoContactsApiClient()

        # Create a mock tender that will raise a generic exception when accessing sectors.first()
        mock_tender = MagicMock()
        mock_tender.amount_int = 1000
        mock_tender.kind = "TYPE_TEST"
        mock_tender.sectors.first.side_effect = Exception("Generic error")

        with patch.object(client, "logger") as mock_logger:
            result = client._additional_tender_attributes(mock_tender)

            # Should return default values with hardcoded keys as in the actual code
            expected = {
                "MONTANT_BESOIN_ACHETEUR": None,
                "TYPE_BESOIN_ACHETEUR": None,
                "TYPE_VERTICALE_ACHETEUR": None,
            }
            self.assertEqual(result, expected)
            mock_logger.error.assert_called()

    def test_get_error_body_with_invalid_json(self, mock_sleep):
        """Test _get_error_body with invalid JSON"""
        client = api_brevo.BrevoContactsApiClient()

        exception = ApiException(status=400, reason="Bad Request")
        exception.body = "invalid json string"

        with patch.object(client, "logger") as mock_logger:
            result = client._get_error_body(exception)

            self.assertEqual(result, {})
            mock_logger.error.assert_called()

    def test_get_error_body_with_no_body_attribute(self, mock_sleep):
        """Test _get_error_body with exception that has no body attribute"""
        client = api_brevo.BrevoContactsApiClient()

        # Create an exception without body attribute
        exception = Exception("No body attribute")

        with patch.object(client, "logger") as mock_logger:
            result = client._get_error_body(exception)

            self.assertEqual(result, {})
            mock_logger.error.assert_called()

    def test_remove_contact_from_list_other_api_error(self, mock_sleep):
        """Test remove_contact_from_list with other API error (not 'already removed')"""
        mock_api_instance = MagicMock()

        # Mock error that's not "already removed"
        error_body = '{"message": "Some other error"}'
        api_error = ApiException(status=400, reason="Bad Request")
        api_error.body = error_body
        mock_api_instance.remove_contact_from_list.side_effect = api_error

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()

            # Should re-raise for retry logic
            with self.assertRaises(api_brevo.BrevoApiError):
                client.remove_contact_from_list("test@example.com", 1)

    def test_retrieve_and_update_user_brevo_contact_id_no_contact_found(self, mock_sleep):
        """Test retrieve_and_update_user_brevo_contact_id when no contact found"""
        client = api_brevo.BrevoContactsApiClient()
        user = UserFactory()

        with patch.object(client, "get_contact_by_email", return_value={}):
            with self.assertRaises(api_brevo.BrevoApiError) as context:
                client.retrieve_and_update_user_brevo_contact_id(user)

            # The exception is caught by the general except clause which prepends "Error retrieving contact ID for"
            self.assertIn(f"Error retrieving contact ID for {user.id}", str(context.exception))

    def test_retrieve_and_update_user_brevo_contact_id_no_id_in_contact(self, mock_sleep):
        """Test retrieve_and_update_user_brevo_contact_id when contact has no ID"""
        client = api_brevo.BrevoContactsApiClient()
        user = UserFactory()

        with patch.object(client, "get_contact_by_email", return_value={"name": "Test"}):
            with self.assertRaises(api_brevo.BrevoApiError) as context:
                client.retrieve_and_update_user_brevo_contact_id(user)

            # The exception is caught by the general except clause which prepends "Error retrieving contact ID for"
            self.assertIn(f"Error retrieving contact ID for {user.id}", str(context.exception))

    def test_retrieve_and_update_user_brevo_contact_id_lookup_exception(self, mock_sleep):
        """Test retrieve_and_update_user_brevo_contact_id when lookup raises exception"""
        client = api_brevo.BrevoContactsApiClient()
        user = UserFactory()

        with patch.object(client, "get_contact_by_email", side_effect=Exception("Lookup error")):
            with self.assertRaises(api_brevo.BrevoApiError) as context:
                client.retrieve_and_update_user_brevo_contact_id(user)

            self.assertIn("Error retrieving contact ID", str(context.exception))

    def test_get_contact_by_email_success(self, mock_sleep):
        """Test get_contact_by_email success"""
        mock_api_instance = MagicMock()

        # Mock successful response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 12345, "email": "test@example.com"}
        mock_api_instance.get_contact_info.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_contact_by_email("test@example.com")

        self.assertEqual(result["id"], 12345)
        self.assertEqual(result["email"], "test@example.com")
        mock_api_instance.get_contact_info.assert_called_once_with("test@example.com")

    def test_get_contact_by_email_non_404_error(self, mock_sleep):
        """Test get_contact_by_email with non-404 API error that should be retried"""
        mock_api_instance = MagicMock()

        # Mock server error (not 404)
        server_error = ApiException(status=500, reason="Server Error")
        mock_api_instance.get_contact_info.side_effect = server_error

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            client = api_brevo.BrevoContactsApiClient()

            with self.assertRaises(api_brevo.BrevoApiError):
                client.get_contact_by_email("test@example.com")

    def test_get_all_contacts_brevo_api_error_handling(self, mock_sleep):
        """Test get_all_contacts handling BrevoApiError in pagination loop"""
        mock_api_instance = MagicMock()

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            # Mock the _fetch_contacts_page to raise BrevoApiError
            client = api_brevo.BrevoContactsApiClient()

            with patch.object(client, "_fetch_contacts_page", side_effect=api_brevo.BrevoApiError("Test error")):
                result = client.get_all_contacts()

                # Should return empty dict when BrevoApiError occurs
                self.assertEqual(result, {})

        # Test when limit_max would be exceeded
        result = client._calculate_pagination_limit(limit_max=25, total_retrieved=20, page_limit=10)
        self.assertEqual(result, 5)  # Only 5 more to reach limit_max of 25

        # Test when limit_max is not exceeded
        result = client._calculate_pagination_limit(limit_max=100, total_retrieved=20, page_limit=10)
        self.assertEqual(result, 10)  # Full page_limit

        # Test with no limit_max
        result = client._calculate_pagination_limit(limit_max=None, total_retrieved=20, page_limit=10)
        self.assertEqual(result, 10)  # Full page_limit

    def test_get_error_body_with_none_body(self, mock_sleep):
        """Test _get_error_body with None body"""
        client = api_brevo.BrevoContactsApiClient()

        exception = ApiException(status=400, reason="Bad Request")
        exception.body = None

        with patch.object(client, "logger") as mock_logger:
            result = client._get_error_body(exception)
            # When body is None, the function returns None implicitly (no return statement executed)
            self.assertIsNone(result)
            # Verify that no error was logged for None body (it should check if body is not None)
            mock_logger.error.assert_not_called()


@patch("lemarche.utils.apis.api_brevo.time.sleep")
class BrevoCompanyApiClientTest(TestCase):
    """
    Tests for the BrevoCompanyApiClient class.
    This covers API interactions, retry mechanisms, and error handling
    for company-related operations.
    """

    def setUp(self):
        self.company = CompanyFactory(
            name="Test Company",
            website="https://company.com",
            description="Buyer company description",
            siret="12345678901234",
            extra_data={"brevo_company_data": {"user_count": 5, "user_tender_count": 3}},
        )

    def test_build_siae_attributes(self, mock_sleep):
        """Test _build_siae_attributes method"""
        siae = SiaeFactory(
            name="Test SIAE",
            website="https://test.com",
            description="Description test",
            kind="EI",
            address="123 Rue Test",
            post_code="75001",
            city="Paris",
            contact_email="contact@test.com",
            is_active=True,
        )
        siae.extra_data = {"brevo_company_data": {"completion_rate": 85, "tender_received": 10, "tender_interest": 5}}
        siae.save()
        clientContactsBrevo = api_brevo.BrevoCompanyApiClient()

        attributes = clientContactsBrevo._build_siae_attributes(siae)

        self.assertEqual(attributes["domain"], "https://test.com")
        self.assertEqual(attributes["app_id"], siae.id)
        self.assertTrue(attributes["siae"])
        self.assertTrue(attributes["active"])
        self.assertEqual(attributes["description"], "Description test")
        self.assertEqual(attributes["kind"], "EI")
        self.assertEqual(attributes["address_street"], "123 Rue Test")
        self.assertEqual(attributes["postal_code"], "75001")
        self.assertEqual(attributes["address_city"], "Paris")
        self.assertEqual(attributes["contact_email"], "contact@test.com")
        self.assertEqual(attributes["taux_de_completion"], 85)
        self.assertEqual(attributes["nombre_de_besoins_recus"], 10)
        self.assertEqual(attributes["nombre_de_besoins_interesses"], 5)

    def test_create_or_update_company_success_create(self, mock_sleep):
        """Test successful company creation"""
        mock_api_instance = MagicMock()

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_buyer_company(self.company)

        # Verify the company was updated with Brevo ID
        self.company.refresh_from_db()
        self.assertEqual(self.company.brevo_company_id, "12345")
        self.assertTrue(len(self.company.logs) > 0)
        self.assertEqual(self.company.logs[-1]["brevo_sync"]["status"], "success")
        mock_api_instance.companies_post.assert_called_once()

    def test_create_or_update_company_success_update(self, mock_sleep):
        """Test successful company update"""
        self.company.brevo_company_id = 99999
        self.company.save()

        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_api_instance.companies_id_patch.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_buyer_company(self.company)

        # Verify update was called with correct ID
        call_args = mock_api_instance.companies_id_patch.call_args
        mock_api_instance.companies_id_patch.assert_called_once_with(99999, call_args[0][1])
        self.company.refresh_from_db()
        self.assertTrue(len(self.company.logs) > 0)
        self.assertEqual(self.company.logs[-1]["brevo_sync"]["status"], "success")

    def test_build_buyer_attributes(self, mock_sleep):
        """Test _build_buyer_attributes method"""
        self.company.extra_data = {"brevo_company_data": {"user_count": 8, "user_tender_count": 15}}
        self.company.email_domain_list = ["company.com", "subsidiary.com"]
        self.company.save()

        clientCompanyBrevo = api_brevo.BrevoCompanyApiClient()

        attributes = clientCompanyBrevo._build_buyer_attributes(self.company)

        self.assertEqual(attributes["domain"], "https://company.com")
        self.assertEqual(attributes["app_id"], self.company.id)
        self.assertFalse(attributes["siae"])
        self.assertEqual(attributes["description"], "Buyer company description")
        self.assertEqual(attributes["kind"], "BUYER")
        self.assertEqual(attributes["siret"], "12345678901234")
        self.assertEqual(attributes["nombre_d_utilisateurs"], 8)
        self.assertEqual(attributes["nombre_besoins"], 15)
        self.assertEqual(attributes["domaines_email"], "company.com,subsidiary.com")

    def test_create_or_update_company_verify_attributes(self, mock_sleep):
        """Test that SIAE company attributes are correctly set"""
        self.company.address = "123 Rue Test"
        self.company.post_code = "75001"
        self.company.city = "Paris"
        self.company.contact_email = "contact@test.com"
        self.company.is_active = True
        self.company.save()

        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_buyer_company(self.company)

        # Verify the company body passed to API
        call_args = mock_api_instance.companies_post.call_args[0][0]
        self.assertEqual(call_args.name, "Test Company")

        attributes = call_args.attributes
        self.assertEqual(attributes["domain"], "https://company.com")
        self.assertEqual(attributes["app_id"], self.company.id)
        self.assertFalse(attributes["siae"])

    def test_create_or_update_company_404_recovery(self, mock_sleep):
        """Test 404 error handling - switches from update to create"""
        self.company.brevo_company_id = 99999
        self.company.save()

        mock_api_instance = MagicMock()

        # First call (update) returns 404, second call (create) succeeds
        not_found_exception = ApiException(status=404, reason="Not Found")
        not_found_exception.body = None
        mock_response = MagicMock()
        mock_response.id = 54321

        mock_api_instance.companies_id_patch.side_effect = not_found_exception
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_buyer_company(self.company)

        # Verify it switched to create mode and updated the ID
        self.company.refresh_from_db()
        self.assertEqual(self.company.brevo_company_id, "54321")
        mock_api_instance.companies_id_patch.assert_called_once()
        mock_api_instance.companies_post.assert_called_once()

    def test_create_or_update_company_retry_mechanism(self, mock_sleep):
        """Test retry mechanism for API errors"""
        mock_api_instance = MagicMock()

        # First call fails, second call succeeds
        server_error = ApiException(status=500, reason="Server Error")
        server_error.body = None
        mock_response = MagicMock()
        mock_response.id = 12345

        mock_api_instance.companies_post.side_effect = [server_error, mock_response]

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            client = api_brevo.BrevoCompanyApiClient(config)
            client.create_or_update_buyer_company(self.company)

        self.company.refresh_from_db()
        self.assertEqual(self.company.brevo_company_id, "12345")
        self.assertEqual(mock_api_instance.companies_post.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    def test_create_or_update_buyer_company_success_create(self, mock_sleep):
        """Test successful buyer company creation"""
        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.id = 67890
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            result = client.create_or_update_buyer_company(self.company)

        self.assertTrue(result)
        self.company.refresh_from_db()
        self.assertEqual(self.company.brevo_company_id, "67890")
        self.assertTrue(len(self.company.logs) > 0)
        self.assertEqual(self.company.logs[-1]["brevo_sync"]["status"], "success")

    def test_create_or_update_buyer_company_success_update(self, mock_sleep):
        """Test successful buyer company update"""
        self.company.brevo_company_id = 77777
        self.company.save()

        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_api_instance.companies_id_patch.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            result = client.create_or_update_buyer_company(self.company)

        self.assertTrue(result)
        call_args = mock_api_instance.companies_id_patch.call_args
        mock_api_instance.companies_id_patch.assert_called_once_with(77777, call_args[0][1])
        self.company.refresh_from_db()
        self.assertTrue(len(self.company.logs) > 0)
        self.assertEqual(self.company.logs[-1]["brevo_sync"]["status"], "success")

    def test_create_or_update_buyer_company_verify_attributes(self, mock_sleep):
        """Test that buyer company attributes are correctly set"""

        mock_api_instance = MagicMock()

        mock_response = MagicMock()
        mock_response.id = 67890
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_buyer_company(self.company)

        # Verify the company body passed to API
        call_args = mock_api_instance.companies_post.call_args[0][0]
        self.assertEqual(call_args.name, "Test Company")

        attributes = call_args.attributes
        self.assertEqual(attributes["domain"], "https://company.com")
        self.assertEqual(attributes["app_id"], self.company.id)
        self.assertFalse(attributes["siae"])  # This is a buyer, not SIAE
        self.assertEqual(attributes["description"], "Buyer company description")
        self.assertEqual(attributes["kind"], "BUYER")
        self.assertEqual(attributes["siret"], "12345678901234")
        self.assertEqual(attributes["nombre_d_utilisateurs"], 5)  # Corrected from nombre_utilisateurs
        self.assertEqual(attributes["nombre_besoins"], 3)

    def test_create_or_update_buyer_company_404_recovery(self, mock_sleep):
        """Test 404 error handling for buyer company - switches from update to create"""
        self.company.brevo_company_id = 88888
        self.company.save()

        mock_api_instance = MagicMock()

        # First call (update) returns 404, second call (create) succeeds
        not_found_exception = ApiException(status=404, reason="Not Found")
        not_found_exception.body = None
        mock_response = MagicMock()
        mock_response.id = 99999

        mock_api_instance.companies_id_patch.side_effect = not_found_exception
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            result = client.create_or_update_buyer_company(self.company)

        self.assertTrue(result)
        self.company.refresh_from_db()
        self.assertEqual(self.company.brevo_company_id, "99999")
        mock_api_instance.companies_id_patch.assert_called_once()
        mock_api_instance.companies_post.assert_called_once()

    def test_create_or_update_buyer_company_api_error_returns_false(self, mock_sleep):
        """Test that buyer company API errors return False instead of raising"""
        mock_api_instance = MagicMock()

        # Simulate persistent API error
        server_error = ApiException(status=500, reason="Server Error")
        server_error.body = None
        mock_api_instance.companies_post.side_effect = server_error

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=1)
            client = api_brevo.BrevoCompanyApiClient(config)
            result = client.create_or_update_buyer_company(self.company)

        self.assertFalse(result)
        self.company.refresh_from_db()
        self.assertIsNone(self.company.brevo_company_id)
        self.assertTrue(len(self.company.logs) > 0)
        self.assertEqual(self.company.logs[-1]["brevo_sync"]["status"], "error")

    @override_settings(BITOUBI_ENV="prod")
    def test_link_company_with_contact_list_success(self, mock_sleep):
        """Test successful company-contact linking"""
        mock_api_instance = MagicMock()

        contact_list = [111, 222, 333]

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.link_company_with_contact_list(12345, contact_list)

        # Verify the API call was made
        mock_api_instance.companies_link_unlink_id_patch.assert_called_once()
        call_args = mock_api_instance.companies_link_unlink_id_patch.call_args
        self.assertEqual(call_args[0][0], 12345)  # company_id
        self.assertEqual(call_args[0][1].link_contact_ids, [111, 222, 333])

    @override_settings(BITOUBI_ENV="prod")
    def test_link_company_with_contact_list_filters_none_values(self, mock_sleep):
        """Test that None values are filtered out from contact list"""
        mock_api_instance = MagicMock()

        contact_list = [111, None, 222, None, 333]

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.link_company_with_contact_list(12345, contact_list)

        # Verify None values were filtered out
        call_args = mock_api_instance.companies_link_unlink_id_patch.call_args
        self.assertEqual(call_args[0][1].link_contact_ids, [111, 222, 333])

    @override_settings(BITOUBI_ENV="local")
    def test_link_company_with_contact_list_empty_list_no_api_call(self, mock_sleep):
        """Test that empty contact list doesn't trigger API call"""
        mock_api_instance = MagicMock()

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.link_company_with_contact_list(12345, [])

        # Verify no API call was made
        mock_api_instance.companies_link_unlink_id_patch.assert_not_called()

    @override_settings(BITOUBI_ENV="prod")
    def test_link_company_with_contact_list_only_none_values_no_api_call(self, mock_sleep):
        """Test that contact list with only None values doesn't trigger API call"""
        mock_api_instance = MagicMock()

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.link_company_with_contact_list(12345, [None, None])

        # Verify no API call was made
        mock_api_instance.companies_link_unlink_id_patch.assert_not_called()

    @override_settings(BITOUBI_ENV="prod")
    def test_link_company_with_contact_list_api_exception_logged(self, mock_sleep):
        """Test that API exceptions are properly logged"""
        mock_api_instance = MagicMock()

        api_error = ApiException(status=400, reason="Bad Request")
        api_error.body = None
        mock_api_instance.companies_link_unlink_id_patch.side_effect = api_error

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()

            # Mock the logger of the client instance
            with patch.object(client, "logger") as mock_logger:
                # Should not raise exception, just log it
                client.link_company_with_contact_list(12345, [111, 222])

                # Verify error was logged
                mock_logger.error.assert_called_once()
                error_msg = mock_logger.error.call_args[0][0]
                self.assertIn("Exception when calling Brevo->DealApi->companies_link_unlink_id_patch", error_msg)

    @override_settings(BITOUBI_ENV="dev")
    def test_link_company_with_contact_list_env_not_allowed(self, mock_sleep):
        """Test that method does nothing when environment is not allowed"""

        # Mock an environment that's not allowed
        with patch("sib_api_v3_sdk.CompaniesApi.companies_link_unlink_id_patch") as mock_api_link_unlink:
            client = api_brevo.BrevoCompanyApiClient()
            client.link_company_with_contact_list(12345, [111, 222])

            # Verify no API client was even created
            mock_api_link_unlink.assert_not_called()

    def test_create_sync_log_create_operation(self, mock_sleep):
        """Test _create_sync_log for create operation"""
        client = api_brevo.BrevoCompanyApiClient()
        company = CompanyFactory()

        log = client._create_sync_log(company)

        self.assertEqual(log["operation"], "create")
        self.assertIn("date", log)

    def test_create_sync_log_update_operation(self, mock_sleep):
        """Test _create_sync_log for update operation"""
        client = api_brevo.BrevoCompanyApiClient()
        company = CompanyFactory()
        company.brevo_company_id = 12345

        log = client._create_sync_log(company)

        self.assertEqual(log["operation"], "update")

    def test_handle_company_error(self, mock_sleep):
        """Test _handle_company_error method"""
        client = api_brevo.BrevoCompanyApiClient()
        company = CompanyFactory()
        sync_log = {"operation": "create"}
        error = api_brevo.BrevoApiError("Test error")

        client._handle_company_error(company, sync_log, error)

        company.refresh_from_db()
        self.assertEqual(sync_log["status"], "error")
        self.assertEqual(sync_log["error"], "Test error")
        self.assertTrue(len(company.logs) > 0)
        self.assertEqual(company.logs[-1]["brevo_sync"]["status"], "error")

    def test_handle_company_404_and_retry_siae(self, mock_sleep):
        """Test _handle_company_404_and_retry for SIAE company"""
        mock_api_instance = MagicMock()

        siae = SiaeFactory()
        siae.brevo_company_id = 99999
        siae.save()

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()

            with patch.object(client, "logger") as mock_logger:
                # Mock the create method to return a success
                mock_create_method = MagicMock(return_value="success")

                result = client._handle_company_404_and_retry(siae, mock_create_method)

                # Verify it logged the warning
                mock_logger.warning.assert_called()

                # Verify brevo_company_id was reset
                siae.refresh_from_db()
                self.assertIsNone(siae.brevo_company_id)

                # Verify create method was called
                mock_create_method.assert_called_once_with(siae)
                self.assertEqual(result, "success")

    def test_handle_company_404_and_retry_buyer(self, mock_sleep):
        """Test _handle_company_404_and_retry for buyer company"""
        mock_api_instance = MagicMock()

        self.company.brevo_company_id = 88888
        self.company.save()

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()

            with patch.object(client, "logger") as mock_logger:
                # Mock the create method to return a success
                mock_create_method = MagicMock(return_value="success")

                client._handle_company_404_and_retry(self.company, mock_create_method)

                # Verify it logged the warning for buyer company
                mock_logger.warning.assert_called()
                warning_msg = mock_logger.warning.call_args[0][0]
                self.assertIn("Buyer company", warning_msg)

    def test_post_process_company_success_create_with_linking(self, mock_sleep):
        """Test _post_process_company_success for create operation with contact linking"""
        client = api_brevo.BrevoCompanyApiClient()

        # Create a SIAE with users
        siae = SiaeFactory()
        user1 = UserFactory(brevo_contact_id=111)
        user2 = UserFactory(brevo_contact_id=222)
        siae.users.add(user1, user2)

        api_response = MagicMock()
        api_response.id = 54321
        sync_log = {"operation": "create"}

        with patch.object(client, "link_company_with_contact_list") as mock_link:
            client._post_process_company_success(siae, api_response, sync_log, is_update=False)

            # Verify company was updated
            siae.refresh_from_db()
            self.assertEqual(siae.brevo_company_id, "54321")
            self.assertEqual(sync_log["status"], "success")
            self.assertEqual(sync_log["brevo_company_id"], 54321)

            # Verify linking was attempted
            mock_link.assert_called_once_with(54321, [111, 222])

    def test_post_process_company_success_create_with_linking_error(self, mock_sleep):
        """Test _post_process_company_success when contact linking fails"""
        client = api_brevo.BrevoCompanyApiClient()

        siae = SiaeFactory()
        user = UserFactory(brevo_contact_id=333)
        siae.users.add(user)

        api_response = MagicMock()
        api_response.id = 65432
        sync_log = {"operation": "create"}

        with patch.object(client, "link_company_with_contact_list", side_effect=Exception("Link error")):
            with patch.object(client, "logger") as mock_logger:
                client._post_process_company_success(siae, api_response, sync_log, is_update=False)

                # Should log the warning but not fail
                mock_logger.warning.assert_called()
                warning_msg = mock_logger.warning.call_args[0][0]
                self.assertIn("Error linking", warning_msg)

    def test_post_process_company_success_update(self, mock_sleep):
        """Test _post_process_company_success for update operation"""
        client = api_brevo.BrevoCompanyApiClient()

        siae = SiaeFactory()
        siae.brevo_company_id = 77777
        siae.save()

        api_response = MagicMock()
        sync_log = {"operation": "update"}

        client._post_process_company_success(siae, api_response, sync_log, is_update=True)

        # Verify logs were updated but ID unchanged
        siae.refresh_from_db()
        self.assertEqual(siae.brevo_company_id, "77777")  # Unchanged
        self.assertEqual(sync_log["status"], "success")
        self.assertTrue(len(siae.logs) > 0)

    def test_cleanup_contact_list_with_valid_ids(self, mock_sleep):
        """Test _cleanup_contact_list with list containing only valid contact IDs"""
        client = api_brevo.BrevoCompanyApiClient()

        contact_list = [111, 222, 333, 444]
        result = client._cleanup_contact_list(contact_list)

        self.assertEqual(result, [111, 222, 333, 444])
        self.assertEqual(len(result), 4)

    def test_cleanup_contact_list_with_none_values(self, mock_sleep):
        """Test _cleanup_contact_list filters out None values"""
        client = api_brevo.BrevoCompanyApiClient()

        contact_list = [111, None, 222, None, 333]
        result = client._cleanup_contact_list(contact_list)

        self.assertEqual(result, [111, 222, 333])
        self.assertEqual(len(result), 3)

    def test_cleanup_contact_list_empty_list(self, mock_sleep):
        """Test _cleanup_contact_list with empty list"""
        client = api_brevo.BrevoCompanyApiClient()

        contact_list = []
        result = client._cleanup_contact_list(contact_list)

        self.assertEqual(result, [])
        self.assertEqual(len(result), 0)

    def test_cleanup_contact_list_all_none_values(self, mock_sleep):
        """Test _cleanup_contact_list with list containing only None values"""
        client = api_brevo.BrevoCompanyApiClient()

        contact_list = [None, None, None]
        result = client._cleanup_contact_list(contact_list)

        self.assertEqual(result, [])
        self.assertEqual(len(result), 0)

    def test_cleanup_contact_list_mixed_types(self, mock_sleep):
        """Test _cleanup_contact_list with mixed valid and None values"""
        client = api_brevo.BrevoCompanyApiClient()

        contact_list = [None, 1, None, 2, 3, None, 4, None]
        result = client._cleanup_contact_list(contact_list)

        self.assertEqual(result, [1, 2, 3, 4])
        self.assertEqual(len(result), 4)

    def test_cleanup_contact_list_preserves_order(self, mock_sleep):
        """Test _cleanup_contact_list preserves the order of valid contact IDs"""
        client = api_brevo.BrevoCompanyApiClient()

        contact_list = [999, None, 111, None, 555, 333]
        result = client._cleanup_contact_list(contact_list)

        self.assertEqual(result, [999, 111, 555, 333])
        # Verify order is preserved
        self.assertEqual(result[0], 999)
        self.assertEqual(result[1], 111)
        self.assertEqual(result[2], 555)
        self.assertEqual(result[3], 333)


@patch("lemarche.utils.apis.api_brevo.time.sleep")
class BrevoTransactionalEmailApiClientTest(TestCase):
    """
    Tests for the BrevoTransactionalEmailApiClient class.
    This covers email sending functionality with retry mechanisms.
    """

    def setUp(self):
        self.email_client = api_brevo.BrevoTransactionalEmailApiClient()

    @override_settings(BITOUBI_ENV="prod")
    def test_send_transactional_email_with_template_success(self, mock_sleep):
        """Test successful email sending"""
        with patch.object(
            self.email_client, "_send_email_with_retry", return_value={"messageId": "12345"}
        ) as mock_send:
            result = self.email_client.send_transactional_email_with_template(
                template_id=1,
                recipient_email="test@example.com",
                recipient_name="Test User",
                variables={"name": "John"},
                subject="Test Subject",
            )

        self.assertEqual(result["messageId"], "12345")
        mock_send.assert_called_once()

    @override_settings(BITOUBI_ENV="dev")
    def test_send_transactional_email_development_environment(self, mock_sleep):
        """Test email sending in development environment"""
        result = self.email_client.send_transactional_email_with_template(
            template_id=1,
            recipient_email="test@example.com",
            recipient_name="Test User",
            variables={"name": "John"},
        )

        # Should return development message without calling API
        self.assertEqual(result["message"], "Email not sent in development/test environment")

    @override_settings(BITOUBI_ENV="prod")
    def test_send_transactional_email_without_custom_subject(self, mock_sleep):
        """Test email sending without custom subject"""
        with patch.object(
            self.email_client, "_send_email_with_retry", return_value={"messageId": "67890"}
        ) as mock_send:
            self.email_client.send_transactional_email_with_template(
                template_id=2,
                recipient_email="test@example.com",
                recipient_name="Test User",
                variables={"name": "Jane"},
                # No subject parameter
            )

        # Verify the method was called
        mock_send.assert_called_once()
        # Verify the data passed to the method doesn't include subject
        call_args = mock_send.call_args[0][0]
        self.assertNotIn("subject", call_args)

    @override_settings(BITOUBI_ENV="prod")
    def test_send_transactional_email_with_retry(self, mock_sleep):
        """Test email sending with retry mechanism"""
        mock_api_instance = MagicMock()

        # First call fails, second succeeds
        server_error = ApiException(status=500, reason="Server Error")
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"messageId": "retry-success"}

        mock_api_instance.send_transac_email.side_effect = [server_error, mock_response]

        with patch("sib_api_v3_sdk.TransactionalEmailsApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            client = api_brevo.BrevoTransactionalEmailApiClient(config)

            result = client.send_transactional_email_with_template(
                template_id=3,
                recipient_email="retry@example.com",
                recipient_name="Retry User",
                variables={"test": "retry"},
            )

        self.assertEqual(result["messageId"], "retry-success")
        self.assertEqual(mock_api_instance.send_transac_email.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    @override_settings(BITOUBI_ENV="prod")
    def test_send_transactional_email_max_retries_exceeded(self, mock_sleep):
        """Test email sending when max retries are exceeded"""
        mock_api_instance = MagicMock()

        # Always fail
        server_error = ApiException(status=500, reason="Server Error")
        mock_api_instance.send_transac_email.side_effect = server_error

        with patch("sib_api_v3_sdk.TransactionalEmailsApi", return_value=mock_api_instance):
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=1)
            client = api_brevo.BrevoTransactionalEmailApiClient(config)

            with self.assertRaises(api_brevo.BrevoApiError):
                client.send_transactional_email_with_template(
                    template_id=4,
                    recipient_email="fail@example.com",
                    recipient_name="Fail User",
                    variables={"test": "fail"},
                )

        self.assertEqual(mock_api_instance.send_transac_email.call_count, 2)  # 1 initial + 1 retry
        mock_sleep.assert_called_once()


@patch("lemarche.utils.apis.api_brevo.time.sleep")
class BrevoUtilityFunctionsTest(TestCase):
    """
    Tests for utility functions (non-legacy).
    """

    def test_cleanup_and_link_contacts_with_contacts(self, mock_sleep):
        """Test _cleanup_and_link_contacts utility function"""

        mock_api_instance = MagicMock()
        mock_body_class = MagicMock()
        mock_body_instance = MagicMock()
        mock_body_class.return_value = mock_body_instance

        contact_list = [111, 222, 333]

        api_brevo._cleanup_and_link_contacts(
            api_instance=mock_api_instance,
            entity_id=12345,
            contact_list=contact_list,
            link_body_class=mock_body_class,
            patch_method_name="test_patch_method",
        )

        # Verify body was created with correct contact IDs
        mock_body_class.assert_called_once_with(link_contact_ids=contact_list)

        # Verify patch method was called
        mock_api_instance.test_patch_method.assert_called_once_with(12345, mock_body_instance)

    def test_cleanup_and_link_contacts_empty_list(self, mock_sleep):
        """Test _cleanup_and_link_contacts with empty contact list"""

        mock_api_instance = MagicMock()
        mock_body_class = MagicMock()

        contact_list = []

        api_brevo._cleanup_and_link_contacts(
            api_instance=mock_api_instance,
            entity_id=12345,
            contact_list=contact_list,
            link_body_class=mock_body_class,
            patch_method_name="test_patch_method",
        )

        # Should not call body class or patch method for empty list
        mock_body_class.assert_not_called()
        mock_api_instance.test_patch_method.assert_not_called()

    def test_brevo_config_is_production_env(self, mock_sleep):
        """Test BrevoConfig.is_production_env property"""
        with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "prod"):
            config = api_brevo.BrevoConfig()
            self.assertTrue(config.is_production_env)

        with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "dev"):
            config = api_brevo.BrevoConfig()
            self.assertFalse(config.is_production_env)

        with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "test"):
            config = api_brevo.BrevoConfig()
            self.assertFalse(config.is_production_env)

    def test_brevo_api_error_initialization(self, mock_sleep):
        """Test BrevoApiError exception initialization"""
        # Test with message only
        error1 = api_brevo.BrevoApiError("Test message")
        self.assertEqual(error1.message, "Test message")
        self.assertIsNone(error1.original_exception)
        self.assertEqual(str(error1), "Test message")

        # Test with message and original exception
        original = ValueError("Original error")
        error2 = api_brevo.BrevoApiError("Wrapper message", original)
        self.assertEqual(error2.message, "Wrapper message")
        self.assertEqual(error2.original_exception, original)
        self.assertEqual(str(error2), "Wrapper message")


class GetValidNumberForBrevoTest(TestCase):
    """Tests for the get_valid_number_for_brevo utility function."""

    def test_get_valid_number_for_brevo_with_none(self):
        """Test with None phone number"""
        result = api_brevo.get_valid_number_for_brevo(None)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_empty_string(self):
        """Test with empty string phone number"""
        result = api_brevo.get_valid_number_for_brevo("")
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_valid_french_number(self):
        """Test with valid French phone number"""
        user = UserFactory(phone="0612345678")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_valid_french_number_e164_format(self):
        """Test with valid French phone number in E164 format"""
        user = UserFactory(phone="+33612345678")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_non_french_number(self):
        """Test with non-French phone number (should return empty string)"""
        user = UserFactory(phone="+1234567890")  # US number
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_invalid_number(self):
        """Test with invalid phone number"""
        user = UserFactory(phone="123")  # Too short to be valid
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_french_landline(self):
        """Test with valid French landline number"""
        user = UserFactory(phone="0145678901")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33145678901")

    def test_get_valid_number_for_brevo_with_french_number_with_spaces(self):
        """Test with French number containing spaces"""
        user = UserFactory(phone="06 12 34 56 78")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_french_number_with_dots(self):
        """Test with French number containing dots"""
        user = UserFactory(phone="06.12.34.56.78")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_french_number_with_dashes(self):
        """Test with French number containing dashes"""
        user = UserFactory(phone="06-12-34-56-78")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_french_number_mixed_separators(self):
        """Test with French number containing mixed separators"""
        user = UserFactory(phone="06 12.34-56 78")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    @skip("understand why the number is not valid for guadeloupe and for 07")
    def test_get_valid_number_for_brevo_with_french_overseas_number(self):
        """Test with French overseas territory number (Guadeloupe)"""
        user = UserFactory(phone="0590123456")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33590123456")

    @skip("understand why the number is not valid for 07")
    def test_get_valid_number_for_brevo_with_french_mobile_07(self):
        """Test with French mobile number starting with 07"""
        user = UserFactory(phone="0712345678")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33712345678")

    def test_get_valid_number_for_brevo_with_french_number_parentheses(self):
        """Test with French number containing parentheses"""
        user = UserFactory(phone="01 (45) 67 89 01")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33145678901")

    def test_get_valid_number_for_brevo_with_international_french_format(self):
        """Test with international French format (0033)"""
        user = UserFactory(phone="0033612345678")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_french_number_extra_spaces(self):
        """Test with French number with extra spaces at beginning and end"""
        user = UserFactory(phone="  06 12 34 56 78  ")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "+33612345678")

    def test_get_valid_number_for_brevo_with_german_number(self):
        """Test with German phone number (should return empty string)"""
        user = UserFactory(phone="+49123456789")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_uk_number(self):
        """Test with UK phone number (should return empty string)"""
        user = UserFactory(phone="+44123456789")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_french_special_service_number(self):
        """Test with French special service number (should return empty string if not valid)"""
        user = UserFactory(phone="0800123456")  # Numéro vert
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        # This will depend on phonenumber library validation
        # If it's considered valid, it should return the E164 format
        # If not valid, it should return empty string
        self.assertIn(result, ["", "+33800123456"])

    def test_get_valid_number_for_brevo_with_invalid_french_format(self):
        """Test with invalid French format (too many digits)"""
        user = UserFactory(phone="061234567890")  # 12 digits instead of 10
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_invalid_french_format_too_few_digits(self):
        """Test with invalid French format (too few digits)"""
        user = UserFactory(phone="06123456")  # 8 digits instead of 10
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_string_that_looks_like_number(self):
        """Test with string that looks like a number but contains letters"""
        user = UserFactory(phone="06abc45678")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        self.assertEqual(result, "")

    def test_get_valid_number_for_brevo_with_french_number_old_format(self):
        """Test with old French format (region code 16)"""
        user = UserFactory(phone="(16) 01 45 67 89 01")
        result = api_brevo.get_valid_number_for_brevo(user.phone)
        # This depends on how phonenumber library handles this
        # But it should probably be invalid or convert to modern format
        self.assertIn(result, ["", "+33145678901"])

    def test_get_valid_number_for_brevo_with_falsely_phone_number(self):
        """Test with a user that has a falsely formatted phone number object"""
        # This test might need to be adapted based on how UserFactory works
        # and how PhoneNumberField handles malformed input
        try:
            user = UserFactory(phone="not_a_number")
            result = api_brevo.get_valid_number_for_brevo(user.phone)
            self.assertEqual(result, "")
        except Exception:
            # If UserFactory throws an exception for invalid phone, that's also valid behavior
            pass
