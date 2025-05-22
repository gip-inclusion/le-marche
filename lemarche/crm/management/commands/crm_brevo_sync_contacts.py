import logging

from django.db import transaction
from tqdm import tqdm

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
    - Progress displayed with tqdm

    Usage:
    python manage.py crm_brevo_sync_contacts --kind-users=BUYER --brevo-list-id=10 --with-existing-contacts --dry-run
    python manage.py crm_brevo_sync_contacts --kind-users=SIAE --brevo-list-id=23
    python manage.py crm_brevo_sync_contacts --recently-updated --brevo-list-id=23
    """

    def add_arguments(self, parser):
        parser.add_argument("--kind-users", dest="kind_users", type=str, help="Filter by user type")
        parser.add_argument(
            "--brevo-list-id",
            dest="brevo_list_id",
            type=int,
            required=True,
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
        parser.add_argument(
            "--batch-size",
            dest="batch_size",
            type=int,
            default=50,
            help="Number of users to process per batch",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulation mode (no changes)")

    def handle(
        self,
        dry_run: bool,
        kind_users: str = None,
        brevo_list_id: int = None,
        with_existing_contacts: bool = False,
        recently_updated: bool = False,
        batch_size: int = 50,
        **options,
    ):
        self.stdout_info("-" * 80)
        self.stdout_info("Synchronizing users with Brevo CRM...")

        # Build the user filtering query
        users_qs = User.objects.all()

        if kind_users:
            users_qs = users_qs.filter(kind=kind_users)
            self.stdout_info(f"Filtering by user type: {kind_users}")

        if recently_updated:
            from datetime import timedelta

            from django.utils import timezone

            two_weeks_ago = timezone.now() - timedelta(weeks=2)
            users_qs = users_qs.filter(updated_at__gte=two_weeks_ago)
            self.stdout_info(f"Filtering by update date: users modified since {two_weeks_ago}")

        # Total number of users to process
        total_users = users_qs.count()
        self.stdout_info(f"Total number of users to process: {total_users}")

        # Get existing contacts in Brevo if needed
        existing_contacts = {}
        if with_existing_contacts:
            self.stdout_info(f"Retrieving existing contacts from Brevo list (ID: {brevo_list_id})...")
            existing_contacts = api_brevo.get_all_users_from_list(list_id=brevo_list_id, verbose=True)
            self.stdout_info(f"Existing contacts in Brevo list: {len(existing_contacts)}")

        if dry_run:
            self.stdout_info("Simulation mode enabled - no changes will be made")
            return

        # Statistics for final report
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "total": total_users}

        # Process users in batches to optimize performance
        for batch_start in tqdm(range(0, total_users, batch_size), desc="Processing users"):
            batch_end = batch_start + batch_size
            batch_users = users_qs[batch_start:batch_end]

            for user in batch_users:
                try:
                    with transaction.atomic():
                        brevo_contact_id = None

                        # Check if user already exists in Brevo
                        if with_existing_contacts:
                            brevo_contact_id = existing_contacts.get(user.email)

                            # If ID is already correctly registered, skip this user
                            if user.brevo_contact_id and user.brevo_contact_id == brevo_contact_id:
                                self.stdout_debug(f"Contact {user.email} already up to date in Brevo")
                                stats["skipped"] += 1
                                continue

                        # If we found an existing Brevo ID, save it
                        if brevo_contact_id:
                            self.stdout_debug(f"Updating Brevo ID for {user.email}: {brevo_contact_id}")
                            user.brevo_contact_id = brevo_contact_id
                            user.save(update_fields=["brevo_contact_id"])
                            stats["updated"] += 1
                        # Otherwise, create a new contact in Brevo
                        else:
                            self.stdout_debug(f"Creating a new contact for {user.email}")
                            result = api_brevo.create_contact(user=user, list_id=brevo_list_id)
                            if result:
                                stats["created"] += 1
                            else:
                                stats["errors"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    self.stdout_error(f"Error processing {user.email}: {str(e)}")

        # Final report
        self.stdout_info("-" * 80)
        self.stdout_info("Synchronization completed! Results:")
        self.stdout_info(
            "- Total processed:"
            + f"{stats['created'] + stats['updated'] + stats['skipped'] + stats['errors']}/{stats['total']}"
        )
        self.stdout_info(f"- Created: {stats['created']}")
        self.stdout_info(f"- Updated: {stats['updated']}")
        self.stdout_info(f"- Skipped (already up to date): {stats['skipped']}")
        self.stdout_info(f"- Errors: {stats['errors']}")
