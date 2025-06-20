import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from lemarche.users.models import User
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Script to send Users to Brevo CRM and/or save their Brevo contact ID

    Features:
    - Synchronizes users of a specific type with Brevo
    - Can check existing contacts before creating new ones
    - Automatic error handling and retries

    Usage:
    python manage.py crm_brevo_sync_contacts --kind-users=BUYER --brevo-list-id=10 --with-existing-contacts --dry-run
    python manage.py crm_brevo_sync_contacts --kind-users=SIAE
    python manage.py crm_brevo_sync_contacts --recently-updated --brevo-list-id=23
    """

    kind_users = None  # Type of users to filter (e.g., BUYER, SIAE)
    recently_updated = False  # Whether to filter users updated in the last two weeks
    brevo_list_id = None  # Brevo list ID to synchronize with
    with_existing_contacts = False  # Whether to check for existing contacts in Brevo
    dry_run = True  # Whether to run in dry run mode (no changes made)

    def __init__(self):
        super().__init__()
        self.stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
        }
        self.brevo_client = api_brevo.BrevoContactsApiClient()

    def add_arguments(self, parser):
        parser.add_argument("--kind-users", dest="kind_users", type=str, help="Filter by user type")
        parser.add_argument(
            "--brevo-list-id",
            dest="brevo_list_id",
            type=int,
            required=False,
            help="Brevo list ID to synchronize with",
        )
        parser.add_argument(
            "--with-existing-contacts",
            dest="with_existing_contacts",
            action="store_true",
            help="Check for existing contacts in Brevo list",
        )
        parser.add_argument(
            "--recently-updated",
            dest="recently_updated",
            action="store_true",
            help="Synchronize only recently updated users",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulation mode (no changes)")

    def _fetch_existing_contacts(self, brevo_list_id):
        """Fetch existing contacts from Brevo if required.
        args:
            brevo_list_id (int): ID of the Brevo list to check.
        returns:
            dict: Dictionary of existing contacts with email as key and Brevo contact ID as value.
            example: {"user@email.com": 13}
        """
        existing_contacts = {}
        if self.with_existing_contacts:
            self.stdout_info(f"Retrieving existing contacts from Brevo list (ID: {brevo_list_id})...")
            if brevo_list_id:
                existing_contacts = self.brevo_client.get_contacts_from_list(list_id=brevo_list_id)
            else:
                existing_contacts = self.brevo_client.get_all_contacts()
            self.stdout_info(f"Existing contacts in Brevo list: {len(existing_contacts)}")
        return existing_contacts

    def _get_current_list_id(self, user):
        """Determine the current list ID based on user kind."""
        if self.brevo_list_id:
            return self.brevo_list_id
        return settings.BREVO_CL_SIGNUP_BUYER_ID if user.kind == User.KIND_BUYER else settings.BREVO_CL_SIGNUP_SIAE_ID

    def _should_skip_user(self, user, existing_contacts):
        """Check if user should be skipped."""
        return (
            self.with_existing_contacts
            and user.brevo_contact_id
            and user.brevo_contact_id == existing_contacts.get(user.email)
        )

    def _build_users_queryset(self):
        """Build the queryset for users based on command arguments."""
        users_qs = User.objects.filter(is_anonymized=False, is_active=True)

        if self.kind_users:
            users_qs = users_qs.filter(kind=self.kind_users)
            self.stdout_info(f"Filtering by user type: {self.kind_users}")

        if self.recently_updated:
            two_weeks_ago = timezone.now() - timedelta(weeks=2)
            users_qs = users_qs.filter(updated_at__gte=two_weeks_ago)
            self.stdout_info(f"Filtering by update date: users modified since {two_weeks_ago}")

        return users_qs

    def _process_single_user(self, user, existing_contacts):
        """Process a single user and update stats directly."""
        try:
            # Check if user should be skipped
            if self._should_skip_user(user, existing_contacts):
                self.stdout_info(f"Contact {user.pk} already up to date in Brevo")
                self.stats["skipped"] += 1
                return

            self.stdout_info(f"Processing user {user.pk}")
            brevo_contact_id = existing_contacts.get(user.email)

            # If we found an existing Brevo ID, save it
            if brevo_contact_id:
                self.stdout_info(f"Updating Brevo ID for {user.pk}: {brevo_contact_id}")
                user.brevo_contact_id = brevo_contact_id
                if not self.dry_run:
                    user.save(update_fields=["brevo_contact_id"])
                self.stats["updated"] += 1
            # Otherwise, create a new contact in Brevo
            else:
                self.stdout_info(f"Creating a new contact for {user.pk}")
                current_list_id = self._get_current_list_id(user)
                if not self.dry_run:
                    try:
                        self.brevo_client.create_contact(user=user, list_id=current_list_id)
                        self.stdout_info(f"Brevo contact created: {user.pk}")
                        self.stats["created"] += 1
                    except api_brevo.BrevoApiError as e:
                        self.stdout_error(f"Failed to create contact for {user.pk}: {e}")
                        self.stats["errors"] += 1
                else:
                    # dry_run case
                    self.stats["created"] += 1
        except Exception as e:
            self.stdout_error(f"Error processing {user.pk}: {str(e)}")
            self.stats["errors"] += 1

    def _display_final_report(self):
        """Display final synchronization report."""
        total_processed = self.stats["created"] + self.stats["updated"] + self.stats["skipped"] + self.stats["errors"]
        self.stdout_info("-" * 80)
        self.stdout_info("Synchronization completed! Results:")
        self.stdout_info(f"- Total processed: {total_processed}/{self.stats['total']}")
        self.stdout_info(f"- Created: {self.stats['created']}")
        self.stdout_info(f"- Updated: {self.stats['updated']}")
        self.stdout_info(f"- Skipped (already up to date): {self.stats['skipped']}")
        self.stdout_info(f"- Errors: {self.stats['errors']}")

    def handle(
        self,
        dry_run: bool,
        kind_users: str = None,
        brevo_list_id: int = None,
        with_existing_contacts: bool = False,
        recently_updated: bool = False,
        **options,
    ):
        self.stdout_info("-" * 80)
        self.stdout_info("Synchronizing users with Brevo CRM...")

        # Initialize command parameters
        self.dry_run = dry_run
        self.with_existing_contacts = with_existing_contacts
        self.kind_users = kind_users
        self.recently_updated = recently_updated
        self.brevo_list_id = brevo_list_id

        # Build the user filtering query
        users_qs = self._build_users_queryset()

        # Total number of users to process
        total_users = users_qs.count()
        self.stdout_info(f"Total number of users to process: {total_users}")

        # Get existing contacts in Brevo if needed
        existing_contacts = self._fetch_existing_contacts(brevo_list_id)

        if dry_run:
            self.stdout_info("Simulation mode enabled - no changes will be made")

        # Statistics for final report
        self.stats["total"] = total_users

        # use .iterator to optimize the chunk processing of large querysets
        for user in users_qs.iterator():
            self._process_single_user(user, existing_contacts)

        # Final report
        self._display_final_report()
