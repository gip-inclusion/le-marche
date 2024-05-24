import time

from lemarche.users.models import User
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Script to send Users to Brevo CRM and/or save their Brevo contact ID

    Usage:
    python manage.py crm_brevo_sync_contacts --kind-users=BUYER --brevo-list-id=10 --with-existing-contacts --dry-run
    python manage.py crm_brevo_sync_contacts --kind-users=SIAE --brevo-list-id=23
    python manage.py crm_brevo_sync_contacts --kind-users=SIAE --brevo-list-id=23
    """

    def add_arguments(self, parser):
        parser.add_argument("--kind-users", dest="kind_users", type=str, required=True, help="set kind of users")
        parser.add_argument(
            "--brevo-list-id",
            dest="brevo_list_id",
            type=int,
            required=True,
            help="set brevo list id",
        )
        parser.add_argument(
            "--with-existing-contacts",
            dest="with_existing_contacts",
            action="store_true",
            help="Check existing contact in brevo list",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, dry_run: bool, kind_users: str, brevo_list_id: int, with_existing_contacts: bool, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to sync with Contact Brevo CRM...")

        users_qs = User.objects.filter(kind=kind_users)

        self.stdout.write(f"Sync User > Brevo: found {users_qs.count()} users {kind_users}.")
        existing_contacts = None
        if with_existing_contacts:
            existing_contacts = api_brevo.get_all_users_from_list(list_id=brevo_list_id)
            self.stdout.write(f"Contacts in brevo list: found {len(existing_contacts)} contacts.")

        if not dry_run:
            for index, user in enumerate(users_qs):
                brevo_contact_id = None

                # if we have existing_contacts in brevo
                if existing_contacts:
                    # try to get id by dictionnary of existing contacts
                    brevo_contact_id = existing_contacts.get(user.email)
                    if user.brevo_contact_id and (user.brevo_contact_id == brevo_contact_id):
                        # skip user
                        self.stdout.write(f"Contact {user.email} already in Brevo.")
                        continue

                # found a brevo_contact_id, save it
                if brevo_contact_id:
                    self.stdout.write(f"Save existing contact {user.email}.")
                    user.brevo_contact_id = brevo_contact_id
                    user.save(update_fields=["brevo_contact_id"])
                # we still don't have a contact id, add to brevo
                else:
                    self.stdout.write(f"Create (or update) and save contact {user.email} in Brevo.")
                    api_brevo.create_contact(user=user, list_id=brevo_list_id)

                if (index % 10) == 0:  # avoid API rate-limiting
                    time.sleep(1)
