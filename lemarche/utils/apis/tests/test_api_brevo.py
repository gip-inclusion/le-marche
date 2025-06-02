from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from sib_api_v3_sdk.rest import ApiException

from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory
from lemarche.utils.apis import api_brevo


class BrevoApiTest(TestCase):
    """
    Tests for the Brevo API utility functions.
    This covers the improved functions that handle API interactions,
    retry mechanisms, and error handling.
    """

    def setUp(self):
        self.user = UserFactory(email="test@example.com")
        self.siae = SiaeFactory()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_success(self, mock_get_api_client):
        """Test successful retrieval of contacts"""
        # Mock API response
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Mock response data
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "contacts": [{"email": "user1@example.com", "id": 1}, {"email": "user2@example.com", "id": 2}]
        }
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts(limit_max=2, since_days=7)

        expected_result = {"user1@example.com": 1, "user2@example.com": 2}
        self.assertEqual(result, expected_result)
        mock_api_instance.get_contacts.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_pagination(self, mock_get_api_client):
        """Test pagination behavior"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Mock responses for pagination
        responses = [
            # First page - full page
            {"contacts": [{"email": f"user{i}@example.com", "id": i} for i in range(1, 51)]},
            # Second page - partial page (end of data)
            {"contacts": [{"email": "user51@example.com", "id": 51}]},
        ]

        mock_api_instance.get_contacts.side_effect = [
            MagicMock(to_dict=lambda: responses[0]),
            MagicMock(to_dict=lambda: responses[1]),
        ]

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts()

        self.assertEqual(len(result), 51)
        self.assertEqual(mock_api_instance.get_contacts.call_count, 2)

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_with_limit_max(self, mock_get_api_client):
        """Test limit_max parameter"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "contacts": [{"email": f"user{i}@example.com", "id": i} for i in range(1, 6)]
        }
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts(limit_max=5)

        self.assertEqual(len(result), 5)
        # Verify that the API was called with the correct limit
        mock_api_instance.get_contacts.assert_called_once()
        call_args = mock_api_instance.get_contacts.call_args
        self.assertEqual(call_args[1]["limit"], 5)

    @patch("lemarche.utils.apis.api_brevo.time.sleep")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_api_exception_with_retry(self, mock_get_api_client, mock_sleep):
        """Test API exception handling with retry mechanism"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # First call raises exception, second call succeeds
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"contacts": [{"email": "user@example.com", "id": 1}]}

        mock_api_instance.get_contacts.side_effect = [ApiException(status=500, reason="Server Error"), mock_response]

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts(max_retries=2)

        self.assertEqual(len(result), 1)
        self.assertEqual(mock_api_instance.get_contacts.call_count, 2)
        mock_sleep.assert_called_once_with(2)  # Exponential backoff

    @patch("lemarche.utils.apis.api_brevo.time.sleep")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_max_retries_exceeded(self, mock_get_api_client, mock_sleep):
        """Test behavior when max retries are exceeded"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Always raise exception
        mock_api_instance.get_contacts.side_effect = ApiException(status=500, reason="Server Error")

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts(max_retries=2)

        self.assertEqual(result, {})
        self.assertEqual(mock_api_instance.get_contacts.call_count, 3)  # Initial call + 2 retries
        self.assertEqual(mock_sleep.call_count, 2)  # 2 retries

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_unexpected_exception(self, mock_get_api_client):
        """Test handling of unexpected exceptions"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Raise unexpected exception
        mock_api_instance.get_contacts.side_effect = Exception("Unexpected error")

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts()

        self.assertEqual(result, {})

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_empty_response(self, mock_get_api_client):
        """Test handling of empty contact list"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"contacts": []}
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts()

        self.assertEqual(result, {})
        mock_api_instance.get_contacts.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_since_days_parameter(self, mock_get_api_client):
        """Test that since_days parameter is correctly passed to API call"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"contacts": []}
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            api_brevo.get_all_contacts(since_days=15)

        # Verify that modified_since parameter was passed
        call_args = mock_api_instance.get_contacts.call_args
        self.assertIn("modified_since", call_args[1])

        # Verify the date is approximately 15 days ago
        modified_since = call_args[1]["modified_since"]
        expected_date = datetime.now() - timedelta(days=15)
        # Allow for small time differences during test execution
        self.assertLess(abs((modified_since - expected_date).total_seconds()), 10)
