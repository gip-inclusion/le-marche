from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings

from django.core.management import call_command
from django.utils import timezone

from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


now = timezone.now()
date_tomorrow = now + timedelta(days=1)
old_date = timezone.now() - timedelta(days=91)
recent_date = now - timedelta(days=10)


@override_settings(BITOUBI_ENV="production", BREVO_API_KEY="fake-key")
class CrmBrevoSyncCompaniesCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Siae instances initialization"""
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_name = SiaeFactory(name="Test Company 1")
        cls.siae_with_user = SiaeFactory(users=[cls.user_siae])
        cls.siae_with_brevo_id = SiaeFactory(
            brevo_company_id="123456789",
        )

        cls.tender_1 = TenderFactory(deadline_date=date_tomorrow)
        cls.tender_2 = TenderFactory(deadline_date=date_tomorrow)

        TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_with_user,
            detail_contact_click_date=recent_date,
        )

        TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_with_brevo_id,
            email_send_date=recent_date,
            detail_contact_click_date=old_date,
        )

        cls.siae_with_user_stats = Siae.objects.with_tender_stats().filter(id=cls.siae_with_user.id).first()
        cls.siae_with_brevo_id_all_stats = (
            Siae.objects.with_tender_stats().filter(id=cls.siae_with_brevo_id.id).first()
        )
        cls.siae_with_brevo_id_recent_stats = (
            Siae.objects.with_tender_stats(since_days=90).filter(id=cls.siae_with_brevo_id.id).first()
        )

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.CompaniesApi")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.Configuration")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.ApiClient")
    def test_new_siaes_are_synced_in_brevo(self, mock_api_client, mock_configuration, mock_companies_api):
        """Test new siaes are synced in brevo"""
        mock_config = MagicMock()
        mock_configuration.return_value = mock_config

        mock_client = MagicMock()
        mock_api_client.return_value = mock_client

        mock_api = MagicMock()
        mock_companies_api.return_value = mock_api

        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api.companies_post.return_value = mock_response

        expected_count = Siae.objects.filter(brevo_company_id__isnull=True).count()

        # Run the command
        call_command("crm_brevo_sync_companies")

        actual_count = mock_api.companies_post.call_count

        self.assertEqual(actual_count, expected_count, f"Expected {expected_count} API calls, got {actual_count}")

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.CompaniesApi")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.Configuration")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.ApiClient")
    def test_siae_has_tender_stats(self, mock_api_client, mock_configuration, mock_companies_api):
        # Setup mock API chain similar to above
        mock_config = MagicMock()
        mock_configuration.return_value = mock_config
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        mock_api = MagicMock()
        mock_companies_api.return_value = mock_api
        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api.companies_post.return_value = mock_response

        self.assertIsNotNone(self.siae_with_user_stats)
        self.assertIsNotNone(self.siae_with_brevo_id_all_stats)

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.CompaniesApi")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.Configuration")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.ApiClient")
    def test_siae_extra_data_is_preserved(self, mock_api_client, mock_configuration, mock_companies_api):
        """Test that creating a company in Brevo preserves existing extra_data"""
        # Setup mock API chain
        mock_config = MagicMock()
        mock_configuration.return_value = mock_config
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        mock_api = MagicMock()
        mock_companies_api.return_value = mock_api
        mock_response = MagicMock()
        mock_response.id = 12345
        mock_api.companies_post.return_value = mock_response

        # Set initial extra_data and ensure other Siaes have brevo_company_id
        initial_extra_data = {"test_data": "test value"}
        self.siae_with_user.extra_data = initial_extra_data.copy()
        self.siae_with_user.save(update_fields=["extra_data"])
        self.siae_with_name.brevo_company_id = "999999"
        self.siae_with_name.save()

        mock_api.companies_post.reset_mock()

        call_command("crm_brevo_sync_companies", recently_updated=True)

        self.siae_with_user.refresh_from_db()

        mock_api.companies_post.assert_called_once()

        self.assertEqual(self.siae_with_user.brevo_company_id, "12345")

        self.assertEqual(self.siae_with_user.extra_data, initial_extra_data)
