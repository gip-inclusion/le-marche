from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import freezegun
from django.core.management import call_command
from django.test import TransactionTestCase
from django.utils import timezone

from lemarche.crm.management.commands.crm_brevo_sync_contacts import Command
from lemarche.users.factories import UserFactory
from lemarche.utils.apis.api_brevo import BrevoApiError


class CrmBrevoSyncContactsCommandTest(TransactionTestCase):
    """Tests for the crm_brevo_sync_contacts management command."""

    def setUp(self):

        # Create test users
        self.user1 = UserFactory(email="user1@example.com", kind="BUYER")
        self.user2 = UserFactory(email="user2@example.com", kind="BUYER")
        self.user3 = UserFactory(email="user3@example.com", kind="SIAE")

        # User with existing Brevo ID
        self.user4 = UserFactory(email="user4@example.com", kind="BUYER", brevo_contact_id=123)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_basic(self, mock_brevo_contacts_client):
        """Test basic synchronization without filters."""
        mock_client_instance = mock_brevo_contacts_client.return_value

        out = StringIO()
        call_command("crm_brevo_sync_contacts", stdout=out)

        # Should process all users (including user4 who already has brevo_contact_id)
        self.assertEqual(mock_client_instance.create_contact.call_count, 4)  # user1, user2, user3, user4

        output = out.getvalue()
        self.assertIn("Total number of users to process: 4", output)
        self.assertIn("Created: 4", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_with_kind_filter(self, mock_brevo_contacts_client):
        """Test synchronization with user kind filter."""
        mock_client_instance = mock_brevo_contacts_client.return_value

        out = StringIO()
        call_command("crm_brevo_sync_contacts", kind_users="BUYER", stdout=out)

        # Should process all BUYER users (including user4 who already has brevo_contact_id)
        self.assertEqual(mock_client_instance.create_contact.call_count, 3)  # user1, user2, user4

        output = out.getvalue()
        self.assertIn("Filtering by user type: BUYER", output)
        self.assertIn("Total number of users to process: 3", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_with_existing_contacts(self, mock_brevo_contacts_client):
        """Test synchronization checking existing contacts in Brevo."""
        mock_client_instance = mock_brevo_contacts_client.return_value
        mock_client_instance.get_contacts_from_list.return_value = {"user1@example.com": 456, "user2@example.com": 789}

        out = StringIO()
        call_command("crm_brevo_sync_contacts", with_existing_contacts=True, brevo_list_id=10, stdout=out)

        # Should update existing users and create new ones
        mock_client_instance.get_contacts_from_list.assert_called_once_with(list_id=10)

        # Refresh users from database
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

        self.assertEqual(self.user1.brevo_contact_id, 456)
        self.assertEqual(self.user2.brevo_contact_id, 789)

        output = out.getvalue()
        self.assertIn("Updated: 2", output)
        self.assertIn("Created: 2", output)  # user3 and user4

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_with_existing_contacts_no_list_id(self, mock_brevo_contacts_client):
        """Test synchronization with existing contacts but no specific list ID."""
        mock_client_instance = mock_brevo_contacts_client.return_value
        mock_client_instance.get_all_contacts.return_value = {"user1@example.com": 456}

        out = StringIO()
        call_command("crm_brevo_sync_contacts", with_existing_contacts=True, stdout=out)

        mock_client_instance.get_all_contacts.assert_called_once()

    def test_sync_contacts_dry_run(self):
        """Test dry run mode - no changes should be made."""
        out = StringIO()
        call_command("crm_brevo_sync_contacts", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Simulation mode enabled - no changes will be made", output)

        # No users should be modified
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertIsNone(self.user1.brevo_contact_id)
        self.assertIsNone(self.user2.brevo_contact_id)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    @freezegun.freeze_time("2023-12-01 12:0:0")
    def test_sync_contacts_recently_updated(self, mock_brevo_contacts_client):
        """Test synchronization of recently updated users only."""

        # Update one user recently
        current_time = timezone.now()

        recent_time = current_time - timedelta(days=5)
        self.user1.updated_at = recent_time
        self.user1.save()

        # Update another user long ago
        old_time = current_time - timedelta(days=30)
        self.user2.updated_at = old_time
        self.user2.save()

        out = StringIO()
        call_command("crm_brevo_sync_contacts", recently_updated=True, stdout=out)

        # Should process only recently updated users
        output = out.getvalue()
        self.assertIn("Filtering by update date", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_with_errors(self, mock_brevo_contacts_client):
        """Test error handling during synchronization."""
        mock_client_instance = mock_brevo_contacts_client.return_value

        # Mock API to raise exception for first user, succeed for others
        def side_effect(user, list_id=None):
            if user.email == "user1@example.com":
                raise Exception("API Error")
            return True

        mock_client_instance.create_contact.side_effect = side_effect

        out = StringIO()
        call_command("crm_brevo_sync_contacts", stdout=out)

        output = out.getvalue()

        self.assertIn("Errors: 1", output)
        self.assertIn("Created: 3", output)
        self.assertIn("Error processing", output)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_batch_processing(self, mock_brevo_contacts_client):
        """Test batch processing functionality."""
        mock_client_instance = mock_brevo_contacts_client.return_value

        out = StringIO()
        call_command("crm_brevo_sync_contacts", stdout=out)

        # Should still process all users
        self.assertEqual(mock_client_instance.create_contact.call_count, 4)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_skip_already_synced(self, mock_brevo_contacts_client):
        """Test skipping users already correctly synced."""
        mock_client_instance = mock_brevo_contacts_client.return_value
        # Mock existing contact that matches user4's brevo_contact_id
        mock_client_instance.get_contacts_from_list.return_value = {
            "user4@example.com": 123  # Same as user4.brevo_contact_id
        }
        # Mock create_contact for other users
        mock_client_instance.create_contact.return_value = True

        out = StringIO()
        call_command("crm_brevo_sync_contacts", with_existing_contacts=True, brevo_list_id=10, stdout=out)

        output = out.getvalue()
        self.assertIn("Skipped (already up to date): 1", output)
        self.assertIn("already up to date in Brevo", output)

    def test_command_arguments(self):
        """Test command argument parsing."""
        command = Command()
        parser = command.create_parser("test", "crm_brevo_sync_contacts")

        # Test with all arguments
        args = parser.parse_args(
            [
                "--kind-users=BUYER",
                "--brevo-list-id=10",
                "--with-existing-contacts",
                "--recently-updated",
                "--dry-run",
            ]
        )

        self.assertEqual(args.kind_users, "BUYER")
        self.assertEqual(args.brevo_list_id, 10)
        self.assertTrue(args.with_existing_contacts)
        self.assertTrue(args.recently_updated)
        self.assertTrue(args.dry_run)

    @patch("lemarche.crm.management.commands.crm_brevo_sync_contacts.api_brevo.BrevoContactsApiClient")
    def test_sync_contacts_api_failure(self, mock_brevo_contacts_client):
        """Test handling of API create contact failure."""
        mock_client_instance = mock_brevo_contacts_client.return_value

        # Mock create_contact to raise an exception
        mock_client_instance.create_contact.side_effect = BrevoApiError("API failure")

        out = StringIO()
        call_command("crm_brevo_sync_contacts", stdout=out)

        output = out.getvalue()
        self.assertIn("Errors: 4", output)  # All 4 users failed
        self.assertIn("Created: 0", output)

    def test_multiple_user_kinds(self):
        """Test with users of different kinds."""
        # Create additional users of different types
        UserFactory(email="admin@example.com", kind="ADMIN")
        UserFactory(email="partner@example.com", kind="PARTNER")

        out = StringIO()
        call_command("crm_brevo_sync_contacts", kind_users="ADMIN", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Total number of users to process: 1", output)
        self.assertIn("Filtering by user type: ADMIN", output)
