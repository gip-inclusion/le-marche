from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase
from django.utils import timezone

from lemarche.companies.factories import CompanyFactory
from lemarche.crm.management.commands.crm_brevo_sync_companies import Command
from lemarche.siaes.factories import SiaeFactory


class CrmBrevoSyncCompaniesCommandTest(TransactionTestCase):
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

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_sync_all_companies_success(self, mock_siae_api, mock_buyer_api):
        """Test successful synchronization of all companies."""

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        # Verify APIs were called
        self.assertTrue(mock_siae_api.call_count > 0)
        self.assertTrue(mock_buyer_api.call_count > 0)
        output = out.getvalue()
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_sync_recently_updated_only(self, mock_api_call):
        """Test synchronization of only recently updated companies."""

        out = StringIO()
        call_command("crm_brevo_sync_companies", recently_updated=True, stdout=out)

        # Verify command ran successfully
        output = out.getvalue()
        self.assertIn("Recently modified SIAEs", output)
        self.assertIn("Recently modified buyer companies", output)
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_dry_run_mode(self, mock_siae_api, mock_buyer_api):
        """Test dry run mode doesn't make actual changes."""
        out = StringIO()
        call_command("crm_brevo_sync_companies", dry_run=True, stdout=out)

        # Verify APIs were not called in dry run mode
        mock_siae_api.assert_not_called()
        mock_buyer_api.assert_not_called()
        output = out.getvalue()
        self.assertIn("Simulation mode enabled", output)

    @patch(
        "lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company",
        side_effect=Exception("API Error"),
    )
    def test_api_error_handling(self, mock_api_call):
        """Test proper error handling when API calls fail."""

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        output = out.getvalue()
        self.assertIn("Error processing", output)
        self.assertIn("Errors:", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_batch_processing(self, mock_siae_api, mock_buyer_api):
        """Test batch processing with custom batch size."""
        mock_siae_api.return_value = None
        mock_buyer_api.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", batch_size=2, stdout=out)

        # Verify command completed successfully with batching
        output = out.getvalue()
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_extra_data_update(self, mock_siae_api, mock_buyer_api):
        """Test that extra_data is properly updated with new statistics."""
        mock_siae_api.return_value = None
        mock_buyer_api.return_value = None

        # Set initial extra_data
        self.siae1.extra_data = {"brevo_company_data": {"completion_rate": 75}}
        self.siae1.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        self.siae1.refresh_from_db()
        self.assertIn("brevo_company_data", self.siae1.extra_data)
        brevo_data = self.siae1.extra_data["brevo_company_data"]
        self.assertIn("completion_rate", brevo_data)
        self.assertIn("tender_received", brevo_data)
        self.assertIn("tender_interest", brevo_data)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_skip_unchanged_data(self, mock_api_call):
        """Test that SIAEs with unchanged data are skipped."""
        self.siae3.extra_data = {
            "brevo_company_data": {
                "completion_rate": None,
                "tender_received": 0,
                "tender_interest": 0,
            }
        }
        self.siae3.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", stdout=out)

        # Verify API was called for buyer companies
        self.assertTrue(mock_api_call.call_count > 0)
        output = out.getvalue()
        self.assertIn("Processing buyer companies", output)
        self.assertIn("Synchronization completed", output)
        self.assertNotIn("Processing SIAE companies", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    def test_sync_buyer_companies_recently_updated(self, mock_api_call):
        """Test synchronization of only recently updated buyer companies."""
        mock_api_call.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", recently_updated=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Recently modified buyer companies", output)
        self.assertIn("Processing buyer companies", output)
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    def test_sync_buyer_companies_dry_run(self, mock_api_call):
        """Test dry run mode for buyer companies."""
        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", dry_run=True, stdout=out)

        # Verify API was not called in dry run mode
        mock_api_call.assert_not_called()
        output = out.getvalue()
        self.assertIn("Simulation mode enabled", output)
        self.assertIn("Processing buyer companies", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    def test_buyer_companies_api_error_handling(self, mock_api_call):
        """Test proper error handling when buyer company API calls fail."""
        mock_api_call.side_effect = Exception("Buyer API Error")

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="buyer", stdout=out)

        output = out.getvalue()
        self.assertIn("Error processing buyer company", output)
        self.assertIn("Errors:", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    def test_buyer_companies_extra_data_update(self, mock_api_call):
        """Test that buyer company extra_data is properly updated with statistics."""
        mock_api_call.return_value = None

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

    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_buyer_company")
    @patch("lemarche.crm.management.commands.crm_brevo_sync_companies.api_brevo.create_or_update_company")
    def test_sync_all_company_types(self, mock_siae_api, mock_buyer_api):
        """Test synchronization of both SIAE and buyer companies."""
        mock_buyer_api.return_value = None
        mock_siae_api.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", company_type="all", stdout=out)

        # Verify both APIs were called
        self.assertTrue(mock_siae_api.call_count > 0)
        self.assertTrue(mock_buyer_api.call_count > 0)

        output = out.getvalue()
        self.assertIn("Processing SIAE companies", output)
        self.assertIn("Processing buyer companies", output)
        self.assertIn("Synchronization completed", output)

    def test_command_arguments(self):
        """Test that command line arguments are properly parsed."""
        command = Command()
        parser = command.create_parser("test", "crm_brevo_sync_companies")

        # Test all arguments
        options = parser.parse_args(["--recently-updated", "--max-retries=5", "--dry-run"])

        self.assertTrue(options.recently_updated)
        self.assertEqual(options.max_retries, 5)
        self.assertTrue(options.dry_run)

    def test_company_type_argument_validation(self):
        """Test that company_type argument accepts valid choices."""
        command = Command()
        parser = command.create_parser("test", "crm_brevo_sync_companies")

        # Test valid company types
        for company_type in ["siae", "buyer", "all"]:
            options = parser.parse_args([f"--company-type={company_type}"])
            self.assertEqual(options.company_type, company_type)
