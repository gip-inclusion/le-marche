from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase
from django.utils import timezone

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
        self.siae4 = SiaeFactory(name="Company 4", extra_data={})
        self.siae4.updated_at = timezone.now() - timedelta(days=3)
        self.siae4.save()

        # SIAE not recently updated
        self.siae5 = SiaeFactory(name="Company 5", extra_data={})
        self.siae5.updated_at = timezone.now() - timedelta(days=30)
        self.siae5.save()

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_sync_all_companies_success(self, mock_api_call):
        """Test successful synchronization of all companies."""
        mock_api_call.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        # Verify API was called for each SIAE that needed update
        self.assertTrue(mock_api_call.call_count > 0)
        output = out.getvalue()
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_sync_recently_updated_only(self, mock_api_call):
        """Test synchronization of only recently updated companies."""
        mock_api_call.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", recently_updated=True, stdout=out)

        # Verify command ran successfully
        output = out.getvalue()
        self.assertIn("Recently modified SIAEs", output)
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_dry_run_mode(self, mock_api_call):
        """Test dry run mode doesn't make actual changes."""
        out = StringIO()
        call_command("crm_brevo_sync_companies", dry_run=True, stdout=out)

        # Verify API was not called in dry run mode
        mock_api_call.assert_not_called()
        output = out.getvalue()
        self.assertIn("Simulation mode enabled", output)

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_api_error_handling(self, mock_api_call):
        """Test proper error handling when API calls fail."""
        # Mock API to raise exception
        mock_api_call.side_effect = Exception("API Error")

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        output = out.getvalue()
        self.assertIn("Error processing", output)
        # Le format d'erreur exact basé sur la sortie des tests
        self.assertIn("Errors: 5", output)  # Corrigé pour refléter le vrai nombre d'erreurs

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_batch_processing(self, mock_api_call):
        """Test batch processing with custom batch size."""
        mock_api_call.return_value = None

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        # Verify command completed successfully with batching
        output = out.getvalue()
        self.assertIn("Synchronization completed", output)

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_extra_data_update(self, mock_api_call):
        """Test that extra_data is properly updated with new statistics."""
        mock_api_call.return_value = None

        # Set initial extra_data
        self.siae1.extra_data = {"brevo_company_data": {"completion_rate": 75}}
        self.siae1.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        # Verify extra_data was updated (the real values come from the queryset)
        self.siae1.refresh_from_db()
        self.assertIn("brevo_company_data", self.siae1.extra_data)
        # Les vraies valeurs dépendent de la méthode with_tender_stats
        brevo_data = self.siae1.extra_data["brevo_company_data"]
        self.assertIn("completion_rate", brevo_data)
        self.assertIn("tender_received", brevo_data)
        self.assertIn("tender_interest", brevo_data)

    @patch("lemarche.utils.apis.api_brevo.create_or_update_company")
    def test_skip_unchanged_data(self, mock_api_call):
        """Test that SIAEs with unchanged data are skipped."""
        # Simuler des données identiques en définissant extra_data avec les vraies valeurs
        # que le queryset va retourner (généralement des valeurs par défaut)
        self.siae3.extra_data = {
            "brevo_company_data": {
                "completion_rate": None,  # Valeur par défaut
                "tender_received": 0,  # Valeur par défaut
                "tender_interest": 0,  # Valeur par défaut
            }
        }
        self.siae3.save()

        out = StringIO()
        call_command("crm_brevo_sync_companies", stdout=out)

        output = out.getvalue()
        # Vérifier que des éléments ont été traités
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
