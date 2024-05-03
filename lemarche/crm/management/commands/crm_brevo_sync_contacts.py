import time

from django.conf import settings

from lemarche.users.models import User

# from lemarche.users.constants import User
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Command script to send Users to Brevo CRM (companies) or set Brevo CRM IDs to Users models

    Usage:
    python manage.py crm_brevo_sync
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--kind-users", dest="kind_users", type=str, default=User.KIND_BUYER, help="set kind of users"
        )
        parser.add_argument(
            "--brevo-list-id",
            dest="brevo_list_id",
            type=int,
            default=settings.BREVO_CL_SIGNUP_BUYER_ID,
            help="set brevo list id",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")
        parser.add_argument(
            "--with-existing-contacts",
            dest="with_existing_contacts",
            action="store_true",
            default=True,
            help="make it with existing contacts in brevo",
        )

    def handle(self, dry_run: bool, kind_users: str, brevo_list_id: int, with_existing_contacts: bool, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to sync with Contact Brevo CRM...")

        # SIAE --> companies
        # Update only the recently updated
        users_qs = User.objects.filter(kind=kind_users)
        progress = 0

        self.stdout.write(f"User: updating our {users_qs.count()} users.")
        existing_contacts = None
        if with_existing_contacts:
            existing_contacts = api_brevo.get_all_users_from_list(list_id=brevo_list_id)
            self.stdout.write(f"Contacts in brevo list: find {len(existing_contacts)} contacts.")

        for user in users_qs:
            if not dry_run:
                brevo_contact_id = None
                if existing_contacts:
                    brevo_contact_id = existing_contacts.get(user.email)
                if brevo_contact_id:
                    user.brevo_contact_id = brevo_contact_id
                else:
                    api_brevo.create_contact(user=user, list_id=brevo_list_id, with_user_save=True)
            progress += 1
            if (progress % 10) == 0:  # avoid API rate-limiting
                time.sleep(1)
