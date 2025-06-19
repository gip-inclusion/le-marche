from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from lemarche.companies.factories import CompanyFactory
from lemarche.crm.management.commands.crm_brevo_sync_companies import Command
from lemarche.siaes.factories import SiaeFactory


# Mock time.sleep globally to speed up tests
@patch("time.sleep")
class CrmBrevoSyncCompaniesCommandTest(TestCase):
    """Tests for the crm_brevo_sync_companies management command."""

    def setUp(self):
        # Create test SIAEs
        self.siae1 = SiaeFactory(name="Company 1", extra_data={})
        self.siae2 = SiaeFactory(name="Company 2", extra_data={})

        # SIAE with existing Brevo ID
        self.siae3 = SiaeFactory(name="Company 3", brevo_company_id=123, extra_data={})

        # SIAE recently updated
        self.siae4 = SiaeFactory(name="Company 4", updated_at=timezone.now() - timedelta(days=3), extra_data={})

        # SIAE not recently updated
        self.siae5 = SiaeFactory(name="Company 5", extra_data={}, updated_at=timezone.now() - timedelta(days=10))
        # Create test buyer companies
        self.buyer_company1 = CompanyFactory(name="Buyer Company 1", extra_data={})
        self.buyer_company2 = CompanyFactory(name="Buyer Company 2", extra_data={})

        # Buyer company with existing Brevo ID
        self.buyer_company3 = CompanyFactory(name="Buyer Company 3", brevo_company_id=456, extra_data={})

        # Buyer company recently updated
        self.buyer_company4 = CompanyFactory(name="Buyer Company 4", extra_data={})
        self.buyer_company4.updated_at = timezone.now() - timedelta(days=5)
        self.buyer_company4.save()

        # Buyer company not recently updated
        self.buyer_company5 = CompanyFactory(name="Buyer Company 5", extra_data={})
        self.buyer_company5.updated_at = timezone.now() - timedelta(days=25)
        self.buyer_company5.save()

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_sync_all_companies_success(self, mock_client_class, mock_sleep):
        """Test successful synchronization of all companies."""
        mock_client = mock_client_class.return_value

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        # Verify APIs were called
        self.assertTrue(mock_client.create_or_update_company.call_count > 0)
        self.assertTrue(mock_client.create_or_update_buyer_company.call_count > 0)
        output = out.getvalue()
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_sync_recently_updated_only(self, mock_client_class, mock_sleep):
        """Test synchronization of only recently updated companies."""

        out = StringIO()
        call_command("crm_brevo_sync_companies", recently_updated=True, stdout=out)

        # Verify command ran successfully
        output = out.getvalue()
        self.assertIn("Recently modified SIAEs", output)
        self.assertIn("Recently modified buyer companies", output)
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_dry_run_mode(self, mock_client_class, mock_sleep):
        """Test dry run mode doesn't make actual changes."""
        mock_client = mock_client_class.return_value

        out = StringIO()
        call_command("crm_brevo_sync_companies", dry_run=True, stdout=out)

        # Verify APIs were not called in dry run mode
        mock_client.create_or_update_company.assert_not_called()
        mock_client.create_or_update_buyer_company.assert_not_called()
        output = out.getvalue()
        self.assertIn("Simulation mode enabled", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_api_error_handling(self, mock_client_class, mock_sleep):
        """Test proper error handling when API calls fail."""
        mock_client = mock_client_class.return_value
        mock_client.create_or_update_company.side_effect = Exception("API Error")

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        output = out.getvalue()
        self.assertIn("Error processing", output)
        self.assertIn("Errors:", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_extra_data_update(self, mock_client_class, mock_sleep):
        """Test that extra_data is properly updated with new statistics."""
        mock_client = mock_client_class.return_value
        mock_client.create_or_update_company.return_value = None
        mock_client.create_or_update_buyer_company.return_value = None

        # Set initial extra_data
        self.siae1.extra_data = {"brevo_company_data": {"completion_rate": 75}}
        self.siae1.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        self.siae1.refresh_from_db()
        self.assertIn("brevo_company_data", self.siae1.extra_data)
        brevo_data = self.siae1.extra_data["brevo_company_data"]
        # Only test for completion_rate as it's the only one that gets updated by default
        self.assertIn("completion_rate", brevo_data)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_skip_unchanged_data(self, mock_client_class, mock_sleep):
        """Test that SIAEs with unchanged data are skipped."""
        mock_client = mock_client_class.return_value

        # Give all SIAEs brevo_company_ids and set their extra_data to match
        # what _prepare_siae_extra_data would calculate for SIAEs with no stats
        for siae in [self.siae1, self.siae2, self.siae3, self.siae4, self.siae5]:
            siae.brevo_company_id = 100 + siae.id
            siae.extra_data = {
                "brevo_company_data": {
                    "completion_rate": 0,  # Default for None completion_rate
                    "tender_received": 0,  # No annotated stats
                    "tender_interest": 0,  # No annotated stats
                }
            }
            siae.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="siae", stdout=out)

        # Verify API was not called because data didn't change
        self.assertEqual(mock_client.create_or_update_company.call_count, 0)
        output = out.getvalue()
        self.assertNotIn("Processing buyer companies", output)
        self.assertIn("Synchronization completed", output)
        self.assertIn("Processing SIAE companies", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_sync_buyer_companies_recently_updated(self, mock_client_class, mock_sleep):
        """Test synchronization of only recently updated buyer companies."""
        mock_client = mock_client_class.return_value
        mock_client.create_or_update_buyer_company.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", recently_updated=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Recently modified buyer companies", output)
        self.assertIn("Processing buyer companies", output)
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_sync_buyer_companies_dry_run(self, mock_client_class, mock_sleep):
        """Test dry run mode for buyer companies."""
        mock_client = mock_client_class.return_value

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", dry_run=True, stdout=out)

        # Verify API was not called in dry run mode
        mock_client.create_or_update_buyer_company.assert_not_called()
        output = out.getvalue()
        self.assertIn("Simulation mode enabled", output)
        self.assertIn("Processing buyer companies", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_buyer_companies_api_error_handling(self, mock_client_class, mock_sleep):
        """Test proper error handling when buyer company API calls fail."""
        mock_client = mock_client_class.return_value
        mock_client.create_or_update_buyer_company.side_effect = Exception("Buyer API Error")

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", stdout=out)

        output = out.getvalue()
        self.assertIn("Error processing buyer company", output)
        self.assertIn("Errors:", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_buyer_companies_extra_data_update(self, mock_client_class, mock_sleep):
        """Test that buyer company extra_data is properly updated with statistics."""
        mock_client = mock_client_class.return_value
        mock_client.create_or_update_buyer_company.return_value = None

        # Set initial extra_data
        self.buyer_company1.extra_data = {"brevo_company_data": {"user_count": 5}}
        self.buyer_company1.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", stdout=out)

        # Verify extra_data was updated
        self.buyer_company1.refresh_from_db()
        self.assertIn("brevo_company_data", self.buyer_company1.extra_data)
        brevo_data = self.buyer_company1.extra_data["brevo_company_data"]
        self.assertIn("user_count", brevo_data)
        self.assertIn("tender_count", brevo_data)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_sync_all_company_types(self, mock_client_class, mock_sleep):
        """Test synchronization of both SIAE and buyer companies."""
        mock_client = mock_client_class.return_value
        mock_client.create_or_update_buyer_company.return_value = None
        mock_client.create_or_update_company.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="all", stdout=out)

        # Verify both APIs were called
        self.assertTrue(mock_client.create_or_update_company.call_count > 0)
        self.assertTrue(mock_client.create_or_update_buyer_company.call_count > 0)

        output = out.getvalue()
        self.assertIn("Processing SIAE companies", output)
        self.assertIn("Processing buyer companies", output)
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_command_arguments(self, mock_client_class, mock_sleep):
        """Test that command line arguments are properly parsed."""
        command = Command()
        parser = command.create_parser("test", "crm_brevo_sync_companies")

        # Test all arguments
        options = parser.parse_args(["--recently-updated", "--max-retries=5", "--dry-run"])

        self.assertTrue(options.recently_updated)
        self.assertEqual(options.max_retries, 5)
        self.assertTrue(options.dry_run)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.BrevoCompanyApiClient")
    def test_company_type_argument_validation(self, mock_client_class, mock_sleep):
        """Test that company_type argument accepts valid choices."""
        command = Command()
        parser = command.create_parser("test", "crm_brevo_sync_companies")

        # Test valid company types
        for company_type in ["siae", "buyer", "all"]:
            options = parser.parse_args([f"--company-type={company_type}"])
            self.assertEqual(options.company_type, company_type)
