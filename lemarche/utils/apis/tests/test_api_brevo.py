from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from sib_api_v3_sdk.rest import ApiException

from lemarche.companies.factories import CompanyFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users.factories import UserFactory
from lemarche.utils.apis import api_brevo
from lemarche.utils.apis.brevo_attributes import CONTACT_ATTRIBUTES


class BrevoContactsApiClientTest(TestCase):
    """
    Tests for the BrevoContactsApiClient class.
    This covers API interactions, retry mechanisms, and error handling
    for contact-related operations.
    """

    def setUp(self):
        self.user = UserFactory(email="test@example.com")
        self.siae = SiaeFactory()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_get_all_contacts_success(self, mock_get_api_client):
        """Test successful retrieval of contacts"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts(limit_max=5)

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
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            client = api_brevo.BrevoContactsApiClient(config)
            result = client.get_all_contacts()

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
            # Use custom config with fewer retries for testing
            config = api_brevo.BrevoConfig(max_retries=2)
            client = api_brevo.BrevoContactsApiClient(config)
            result = client.get_all_contacts()

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
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts()

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
            client = api_brevo.BrevoContactsApiClient()
            result = client.get_all_contacts()

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
            client = api_brevo.BrevoContactsApiClient()
            response = client.create_contact(self.user, list_id=1)

        # Verify the API response is returned
        self.assertEqual(response["id"], 12345)
        mock_api_instance.create_contact.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_contact_with_tender(self, mock_get_api_client):
        """Test contact creation with tender information"""
        sector = SectorFactory(name="Informatique")
        tender = TenderFactory(amount_exact=50000, kind="PRESTA", source="TALLY")
        tender.sectors.add(sector)

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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

    def test_create_contact_already_has_brevo_id(self):
        """Test contact creation when user already has Brevo ID"""
        self.user.brevo_contact_id = 99999
        self.user.save()

        # Should not raise any exception
        c = api_brevo.BrevoContactsApiClient()
        c.create_contact(self.user, list_id=1)

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
            c = api_brevo.BrevoContactsApiClient()
            response = c.create_contact(self.user, list_id=1)

        # The user's brevo_contact_id should be automatically updated by the client method
        self.user.refresh_from_db()
        self.assertEqual(self.user.brevo_contact_id, 55555)

        # Response should contain the retrieved ID
        self.assertEqual(response["id"], 55555)
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
                # Use custom config with fewer retries for testing
                config = api_brevo.BrevoConfig(max_retries=2)
                c = api_brevo.BrevoContactsApiClient(config)
                c.create_contact(self.user, list_id=1)

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
                # Use custom config with fewer retries for testing
                config = api_brevo.BrevoConfig(max_retries=1)
                c = api_brevo.BrevoContactsApiClient(config)
                c.create_contact(self.user, list_id=1)

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


class BrevoCompanyApiClientTest(TestCase):
    """
    Tests for the BrevoCompanyApiClient class.
    This covers API interactions, retry mechanisms, and error handling
    for company-related operations.
    """

    def setUp(self):
        self.siae = SiaeFactory(name="Test SIAE", website="https://test.com")
        self.company = CompanyFactory(name="Test Company", website="https://company.com")

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_company_success_create(self, mock_get_api_client):
        """Test successful SIAE company creation"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_company(self.siae)

        # Verify the SIAE was updated with Brevo ID
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.brevo_company_id, "12345")
        self.assertTrue(len(self.siae.logs) > 0)
        self.assertEqual(self.siae.logs[-1]["brevo_sync"]["status"], "success")
        mock_api_instance.companies_post.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_company_success_update(self, mock_get_api_client):
        """Test successful SIAE company update"""
        self.siae.brevo_company_id = 99999
        self.siae.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_api_instance.companies_id_patch.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_company(self.siae)

        # Verify update was called with correct ID
        call_args = mock_api_instance.companies_id_patch.call_args
        mock_api_instance.companies_id_patch.assert_called_once_with(99999, call_args[0][1])
        self.siae.refresh_from_db()
        self.assertTrue(len(self.siae.logs) > 0)
        self.assertEqual(self.siae.logs[-1]["brevo_sync"]["status"], "success")

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_company_verify_attributes(self, mock_get_api_client):
        """Test that SIAE company attributes are correctly set"""
        self.siae.description = "Une SIAE de test"
        self.siae.kind = "EI"
        self.siae.address = "123 Rue Test"
        self.siae.post_code = "75001"
        self.siae.city = "Paris"
        self.siae.contact_email = "contact@test.com"
        self.siae.is_active = True
        self.siae.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_company(self.siae)

        # Verify the company body passed to API
        call_args = mock_api_instance.companies_post.call_args[0][0]
        self.assertEqual(call_args.name, "Test SIAE")

        attributes = call_args.attributes
        self.assertEqual(attributes["domain"], "https://test.com")
        self.assertEqual(attributes["app_id"], self.siae.id)
        self.assertTrue(attributes["siae"])
        self.assertTrue(attributes["active"])
        self.assertEqual(attributes["description"], "Une SIAE de test")
        self.assertEqual(attributes["kind"], "EI")
        self.assertEqual(attributes["address_street"], "123 Rue Test")
        self.assertEqual(attributes["address_post_code"], "75001")
        self.assertEqual(attributes["address_city"], "Paris")
        self.assertEqual(attributes["contact_email"], "contact@test.com")

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_company_404_recovery(self, mock_get_api_client):
        """Test 404 error handling - switches from update to create"""
        self.siae.brevo_company_id = 99999
        self.siae.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # First call (update) returns 404, second call (create) succeeds
        not_found_exception = ApiException(status=404, reason="Not Found")
        not_found_exception.body = None
        mock_response = MagicMock()
        mock_response.id = 54321

        mock_api_instance.companies_id_patch.side_effect = not_found_exception
        mock_api_instance.companies_post.return_value = mock_response

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            client = api_brevo.BrevoCompanyApiClient()
            client.create_or_update_company(self.siae)

        # Verify it switched to create mode and updated the ID
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.brevo_company_id, "54321")
        mock_api_instance.companies_id_patch.assert_called_once()
        mock_api_instance.companies_post.assert_called_once()

    @patch("lemarche.utils.apis.api_brevo.time.sleep")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_company_retry_mechanism(self, mock_get_api_client, mock_sleep):
        """Test retry mechanism for API errors"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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
            client.create_or_update_company(self.siae)

        self.siae.refresh_from_db()
        self.assertEqual(self.siae.brevo_company_id, "12345")
        self.assertEqual(mock_api_instance.companies_post.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    @patch("lemarche.utils.apis.api_brevo.time.sleep")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_company_max_retries_exceeded(self, mock_get_api_client, mock_sleep):
        """Test behavior when max retries are exceeded"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        # Always fail
        server_error = ApiException(status=500, reason="Server Error")
        server_error.body = None
        mock_api_instance.companies_post.side_effect = server_error

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            with self.assertRaises(api_brevo.BrevoApiError):
                # Use custom config with fewer retries for testing
                config = api_brevo.BrevoConfig(max_retries=2)
                client = api_brevo.BrevoCompanyApiClient(config)
                client.create_or_update_company(self.siae)

        self.siae.refresh_from_db()
        self.assertIsNone(self.siae.brevo_company_id)
        self.assertTrue(len(self.siae.logs) > 0)
        self.assertEqual(self.siae.logs[-1]["brevo_sync"]["status"], "error")
        self.assertEqual(mock_api_instance.companies_post.call_count, 3)  # 1 initial + 2 retries

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_buyer_company_success_create(self, mock_get_api_client):
        """Test successful buyer company creation"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_buyer_company_success_update(self, mock_get_api_client):
        """Test successful buyer company update"""
        self.company.brevo_company_id = 77777
        self.company.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_buyer_company_verify_attributes(self, mock_get_api_client):
        """Test that buyer company attributes are correctly set"""
        self.company.description = "Une entreprise acheteuse"
        self.company.siret = "12345678901234"
        self.company.extra_data = {"brevo_company_data": {"user_count": 5, "user_tender_count": 3}}
        self.company.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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
        self.assertEqual(attributes["description"], "Une entreprise acheteuse")
        self.assertEqual(attributes["kind"], "BUYER")
        self.assertEqual(attributes["siret"], "12345678901234")
        self.assertEqual(attributes["nombre_utilisateurs"], 5)
        self.assertEqual(attributes["nombre_besoins"], 3)

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_buyer_company_404_recovery(self, mock_get_api_client):
        """Test 404 error handling for buyer company - switches from update to create"""
        self.company.brevo_company_id = 88888
        self.company.save()

        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_create_or_update_buyer_company_api_error_returns_false(self, mock_get_api_client):
        """Test that buyer company API errors return False instead of raising"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

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

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_link_company_with_contact_list_success(self, mock_get_api_client):
        """Test successful company-contact linking"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        contact_list = [111, 222, 333]

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "local"):
                client = api_brevo.BrevoCompanyApiClient()
                client.link_company_with_contact_list(12345, contact_list)

        # Verify the API call was made
        mock_api_instance.companies_link_unlink_id_patch.assert_called_once()
        call_args = mock_api_instance.companies_link_unlink_id_patch.call_args
        self.assertEqual(call_args[0][0], 12345)  # company_id
        self.assertEqual(call_args[0][1].link_contact_ids, [111, 222, 333])

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_link_company_with_contact_list_filters_none_values(self, mock_get_api_client):
        """Test that None values are filtered out from contact list"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        contact_list = [111, None, 222, None, 333]

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "local"):
                client = api_brevo.BrevoCompanyApiClient()
                client.link_company_with_contact_list(12345, contact_list)

        # Verify None values were filtered out
        call_args = mock_api_instance.companies_link_unlink_id_patch.call_args
        self.assertEqual(call_args[0][1].link_contact_ids, [111, 222, 333])

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_link_company_with_contact_list_empty_list_no_api_call(self, mock_get_api_client):
        """Test that empty contact list doesn't trigger API call"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "local"):
                client = api_brevo.BrevoCompanyApiClient()
                client.link_company_with_contact_list(12345, [])

        # Verify no API call was made
        mock_api_instance.companies_link_unlink_id_patch.assert_not_called()

    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_link_company_with_contact_list_only_none_values_no_api_call(self, mock_get_api_client):
        """Test that contact list with only None values doesn't trigger API call"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "local"):
                client = api_brevo.BrevoCompanyApiClient()
                client.link_company_with_contact_list(12345, [None, None])

        # Verify no API call was made
        mock_api_instance.companies_link_unlink_id_patch.assert_not_called()

    @patch("lemarche.utils.apis.api_brevo.logger")
    @patch("lemarche.utils.apis.api_brevo.get_api_client")
    def test_link_company_with_contact_list_api_exception_logged(self, mock_get_api_client, mock_logger):
        """Test that API exceptions are properly logged"""
        mock_api_instance = MagicMock()
        mock_client = MagicMock()
        mock_get_api_client.return_value = mock_client

        api_error = ApiException(status=400, reason="Bad Request")
        api_error.body = None
        mock_api_instance.companies_link_unlink_id_patch.side_effect = api_error

        with patch("sib_api_v3_sdk.CompaniesApi", return_value=mock_api_instance):
            with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", "local"):
                client = api_brevo.BrevoCompanyApiClient()
                # Should not raise exception, just log it
                client.link_company_with_contact_list(12345, [111, 222])

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Exception when calling Brevo->DealApi->companies_link_unlink_id_patch", error_msg)

    def test_link_company_with_contact_list_env_not_allowed(self):
        """Test that method does nothing when environment is not allowed"""
        from lemarche.utils.apis.api_brevo import ENV_NOT_ALLOWED

        # Mock an environment that's not allowed
        with patch("lemarche.utils.apis.api_brevo.settings.BITOUBI_ENV", ENV_NOT_ALLOWED[0]):
            with patch("lemarche.utils.apis.api_brevo.get_api_client") as mock_get_api_client:
                client = api_brevo.BrevoCompanyApiClient()
                client.link_company_with_contact_list(12345, [111, 222])

                # Verify no API client was even created
                mock_get_api_client.assert_not_called()
