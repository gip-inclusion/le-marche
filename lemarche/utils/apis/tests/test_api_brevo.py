from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from sib_api_v3_sdk.rest import ApiException

from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
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
            "contacts": [{"email": "user1@example.com", "id": 1}, {"email": "user2@example.com", "id": 2}],
            "count": 2,
        }
        mock_api_instance.get_contacts.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            result = api_brevo.get_all_contacts(limit_max=2, since_days=7)

        expected_result = {"user1@example.com": 1, "user2@example.com": 2}
        self.assertEqual(result, expected_result)
        mock_api_instance.get_contacts.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_pagination(self, mock_get_api_client):
        """Test pagination functionality"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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
            result = api_brevo.get_all_contacts(page_limit=5)

        # Verify that all contacts were retrieved
        self.assertEqual(len(result), 8)
        expected_result = {f"user{i}@example.com": i for i in range(1, 9)}
        self.assertEqual(result, expected_result)

        # Verify that the API was called 2 times with correct parameters
        self.assertEqual(mock_api_instance.get_contacts.call_count, 2)

        # Verify parameters of first call (offset=0, limit=5)
        first_call_args = mock_api_instance.get_contacts.call_args_list[0]
        self.assertEqual(first_call_args[1]["offset"], 0)
        self.assertEqual(first_call_args[1]["limit"], 5)

        # Verify parameters of second call (offset=5, limit=5)
        second_call_args = mock_api_instance.get_contacts.call_args_list[1]
        self.assertEqual(second_call_args[1]["offset"], 5)
        self.assertEqual(second_call_args[1]["limit"], 5)

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_with_limit_max(self, mock_get_api_client):
        """Test limit_max parameter"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "contacts": [{"email": f"user{i}@example.com", "id": i} for i in range(1, 6)],
            "count": 100,  # Total available
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
        mock_sleep.assert_called_once_with(5)  # retry delay

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
        mock_response.to_dict.return_value = {"contacts": [], "count": 0}
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

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_success(self, mock_get_api_client):
        """Test successful contact creation"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 12345}
        mock_api_instance.create_contact.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            api_brevo.create_contact(self.user, list_id=1)

        self.user.refresh_from_db()
        self.assertEqual(self.user.brevo_contact_id, 12345)
        mock_api_instance.create_contact.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_with_tender(self, mock_get_api_client):
        """Test contact creation with tender information"""

        sector = SectorFactory(name="Informatique")
        tender = TenderFactory(amount_exact=50000, kind="PRESTA", source="TALLY")  # Utiliser une valeur plus courte
        tender.sectors.add(sector)

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 12345}
        mock_api_instance.create_contact.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            api_brevo.create_contact(self.user, list_id=1, tender=tender)

        # Verify that tender attributes were included in the call
        call_args = mock_api_instance.create_contact.call_args[0][0]
        self.assertEqual(call_args.attributes["MONTANT_BESOIN_ACHETEUR"], 50000)
        self.assertEqual(call_args.attributes["TYPE_BESOIN_ACHETEUR"], "PRESTA")
        self.assertEqual(call_args.attributes["TYPE_VERTICALE_ACHETEUR"], "Informatique")

    def test_create_contact_already_has_brevo_id(self):
        """Test contact creation when user already has Brevo ID"""
        self.user.brevo_contact_id = 99999
        self.user.save()

        # Should not raise any exception
        api_brevo.create_contact(self.user, list_id=1)

    @patch("lemarche.utils.apis.api_brevo.BrevoContactsApiClient.get_contact_by_email")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_duplicate_error_with_recovery(self, mock_get_api_client, mock_get_contact_by_email):
        """Test handling of duplicate contact error with successful ID recovery"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Mock duplicate error response
        error_body = '{"code": "duplicate_parameter", "message": "Contact already exists"}'
        duplicate_exception = ApiException(status=400, reason="Bad Request")
        duplicate_exception.body = error_body
        mock_api_instance.create_contact.side_effect = duplicate_exception

        # Mock successful contact lookup
        mock_get_contact_by_email.return_value = {"id": 55555}

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            api_brevo.create_contact(self.user, list_id=1)

        self.user.refresh_from_db()
        self.assertEqual(self.user.brevo_contact_id, 55555)
        mock_get_contact_by_email.assert_called_once_with(self.user.email)

    @patch("lemarche.utils.apis.api_brevo.time.sleep")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_rate_limit_with_retry(self, mock_get_api_client, mock_sleep):
        """Test retry mechanism for rate limiting"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # First call rate limited, second call succeeds
        rate_limit_exception = ApiException(status=429, reason="Rate Limit")
        rate_limit_exception.body = None  # Ajouter l'attribut body
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 77777}

        mock_api_instance.create_contact.side_effect = [rate_limit_exception, mock_response]

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            api_brevo.create_contact(self.user, list_id=1, max_retries=2)

        self.user.refresh_from_db()
        self.assertEqual(self.user.brevo_contact_id, 77777)
        self.assertEqual(mock_api_instance.create_contact.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.time.sleep")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_max_retries_exceeded(self, mock_get_api_client, mock_sleep):
        """Test behavior when max retries are exceeded"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Always return server error
        server_error = ApiException(status=500, reason="Internal Server Error")
        server_error.body = None  # Ajouter l'attribut body
        mock_api_instance.create_contact.side_effect = server_error

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            with self.assertRaises(api_brevo.BrevoApiError):
                api_brevo.create_contact(self.user, list_id=1, max_retries=2)

        self.user.refresh_from_db()
        self.assertIsNone(self.user.brevo_contact_id)
        self.assertEqual(mock_api_instance.create_contact.call_count, 3)  # 1 initial + 2 retries
        self.assertEqual(mock_sleep.call_count, 2)  # 2 retries avec max_retries=2

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_malformed_error_response(self, mock_get_api_client):
        """Test handling of malformed JSON error response"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Mock error with malformed JSON body
        error_exception = ApiException(status=400, reason="Bad Request")
        error_exception.body = "invalid json"
        mock_api_instance.create_contact.side_effect = error_exception

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            with self.assertRaises(api_brevo.BrevoApiError):
                api_brevo.create_contact(self.user, list_id=1, max_retries=1)

        self.user.refresh_from_db()
        self.assertIsNone(self.user.brevo_contact_id)

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_verify_attributes(self, mock_get_api_client):
        """Test that contact attributes are correctly set"""
        self.user.last_name = "Dupont"
        self.user.first_name = "Jean"
        self.user.company_name = "ACME Corp"
        self.user.phone = "+33123456789"
        self.user.buyer_kind_detail = "ENTREPRISE"
        self.user.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 88888}
        mock_api_instance.create_contact.return_value = mock_response

        with patch("sib_api_v3_sdk.ContactsApi", return_value=mock_api_instance):
            api_brevo.create_contact(self.user, list_id=1)

        # Verify the contact object passed to API
        call_args = mock_api_instance.create_contact.call_args[0][0]
        self.assertEqual(call_args.email, self.user.email)
        self.assertEqual(call_args.list_ids, [1])
        self.assertEqual(call_args.ext_id, str(self.user.id))
        self.assertTrue(call_args.update_enabled)

        # Verify attributes
        attributes = call_args.attributes
        self.assertEqual(attributes["NOM"], "Dupont")
        self.assertEqual(attributes["PRENOM"], "Jean")
        self.assertEqual(attributes["NOM_ENTREPRISE"], "Acme corp")
        self.assertEqual(attributes["TYPE_ORGANISATION"], "ENTREPRISE")
        self.assertEqual(attributes["SMS"], "+33123456789")
