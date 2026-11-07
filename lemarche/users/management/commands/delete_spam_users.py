import collections

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.users.constants import KIND_SIAE
from lemarche.users.models import User
from lemarche.utils.db import secure_delete


class Command(BaseCommand):
    """Update and anonymize inactive users past a defined inactivity period"""

    def add_arguments(self, parser):
        parser.add_argument("--wet-run", action="store_true", help="Appliquer les changements en base de données")

    def handle(self, wet_run, **options):
        user_qs = User.objects.filter(
            kind=KIND_SIAE,
            siaeuser__isnull=True,  # With no structure
            siaeuserrequest__isnull=True,  # no initiated request
            siaeuserrequest_assignee__isnull=True,  # no assigned request
            tenders__isnull=True,  # no tender
            conversation__isnull=True,  # no conversation
            favorite_lists__isnull=True,  # no favorite list
            sectors__isnull=True,  # No sector
            created_at__lte=timezone.now() - relativedelta(days=7),
        ).exclude(emailaddress__verified=True)
        self.stdout.write(f"Found {user_qs.count()} SIAE spam accounts")
        if wet_run:
            deleted = secure_delete(
                user_qs,
                [
                    "users.User",
                    "account.EmailAddress",
                    "conversations.TemplateTransactionalSendLog",  # Reverse Generic relation on User
                    "notes.Note",  # GenericForeignKey to User
                ],
            )

            if deleted:
                sorted_deleted = dict(collections.OrderedDict(sorted(deleted.items())))
                log = f"Deleted {deleted.get('users.User', 0)} users ({sorted_deleted})"
                self.stdout.write(log)
