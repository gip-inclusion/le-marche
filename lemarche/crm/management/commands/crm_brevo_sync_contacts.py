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
    python manage.py crm_brevo_sync_contacts --dry-run
    python manage.py crm_brevo_sync_contacts --brevo-list-id=23 --kind-users=SIAE
    python manage.py crm_brevo_sync_contacts --brevo-list-id=10 --kind-users=SIAE --dry-run
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--kind-users", dest="kind_users", type=str, default=User.KIND_SIAE, help="set kind of users"
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
            type=bool,
            default=True,
            help="make it with existing contacts in brevo",
        )

    def handle(self, dry_run: bool, kind_users: str, brevo_list_id: int, with_existing_contacts: bool, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to sync with Contact Brevo CRM...")

        users_qs = User.objects.filter(kind=kind_users)
        progress = 0

        self.stdout.write(f"User: find {users_qs.count()} users {kind_users}.")
        existing_contacts = None
        if with_existing_contacts:
            existing_contacts = api_brevo.get_all_users_from_list(list_id=brevo_list_id)
            self.stdout.write(f"Contacts in brevo list: find {len(existing_contacts)} contacts.")

        if not dry_run:
            for user in users_qs:
                brevo_contact_id = None
                # if we have existing_contacts in brevo
                if existing_contacts:
                    # try to get id by dictionnary of existing contacts
                    brevo_contact_id = existing_contacts.get(user.email)
                # if we still not have contact id
                if not brevo_contact_id:
                    self.stdout.write(f"Create and save contact {user.email} in Brevo.")
                    api_brevo.create_contact(user=user, list_id=brevo_list_id, with_user_save=True)
                # if we already have the brevo_contact_id, we can simply save it
                else:
                    self.stdout.write(f"Save existing contact {user.email}.")
                    user.brevo_contact_id = brevo_contact_id
                    user.save()

                progress += 1
                if (progress % 10) == 0:  # avoid API rate-limiting
                    time.sleep(1)
