from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.expressions import Exists, F, OuterRef, Q
from django.template import defaulttags
from django.utils import timezone

from lemarche.conversations.models import TemplateTransactional
from lemarche.stats.models import StatsUser
from lemarche.tenders.models import Tender
from lemarche.users.constants import KIND_ADMIN
from lemarche.users.models import User
from lemarche.utils.db import secure_delete


class Command(BaseCommand):
    """Update and anonymize inactive users past a defined inactivity period"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="La commande est exécutée sans que les modifications soient transmises à la base",
        )

    def handle(self, *args, **options):
        self.user_qs = User.objects.exclude(kind=KIND_ADMIN)
        self.reset_notified_users_with_recent_activity(dry_run=options["dry_run"])
        self.notify_inactive_users(dry_run=options["dry_run"])
        self.delete_old_users(dry_run=options["dry_run"])
        self.anonymize_stats(dry_run=options["dry_run"])

    def get_users_with_last_action(self, inactive_since):
        recent_tender = Tender.objects.filter(updated_at__gt=inactive_since, author_id=OuterRef("pk"))
        return self.user_qs.filter(
            Q(last_login__lte=inactive_since) | Q(last_login=None, date_joined__lte=inactive_since)
        ).filter(~Exists(recent_tender))

    @transaction.atomic
    def reset_notified_users_with_recent_activity(self, dry_run: bool):
        """Reset pending deletion notice date for users who recently logged in."""

        qs = self.user_qs.exclude(pending_deletion_notice_date=None).filter(
            last_login__gte=F("pending_deletion_notice_date")
        )

        if dry_run:
            self.stdout.write(
                f"Dry-run: reset des utilisateurs: {qs.count()} se sont reconnectés depuis la notification"
            )
            return

        updated = qs.update(pending_deletion_notice_date=None)
        self.stdout.write(f"Reset des utilisateurs: {updated} se sont reconnectés depuis la notification")

    @transaction.atomic
    def notify_inactive_users(self, dry_run: bool):
        """Send an email to warn inactive users their account will soon be deleted."""

        email_template = TemplateTransactional.objects.get(code="USER_DELETION_WARNING")
        expiry_date = timezone.now() - relativedelta(months=settings.INACTIVE_USER_TIMEOUT_IN_MONTHS)
        warning_date = expiry_date + relativedelta(months=settings.INACTIVE_USER_WARNING_DELAY_IN_MONTHS)

        # Users that have already received the mail are excluded
        users_to_warn = self.get_users_with_last_action(warning_date).filter(
            is_active=True,
            pending_deletion_notice_date=None,
        )

        if dry_run:
            self.stdout.write(f"Dry-run: avertissement des utilisateurs: {users_to_warn.count()} auraient été avertis")
            return  # exit before sending emails

        # send an email to warn users
        now = timezone.now()
        deletion_date = now + relativedelta(months=settings.INACTIVE_USER_WARNING_DELAY_IN_MONTHS)
        for user in users_to_warn:
            email_template.send_transactional_email(
                recipient_email=user.email,
                recipient_name=user.full_name,
                variables={
                    "user_full_name": user.full_name,
                    "deletion_date": defaulttags.date(deletion_date),  # natural date
                },
                recipient_content_object=user,
            )

        # update users with the date they were notified of the pending deletion of their account
        updated = users_to_warn.update(pending_deletion_notice_date=now)

        self.stdout.write(f"Avertissement des utilisateurs: {updated} ont été avertis")

    @transaction.atomic
    def delete_old_users(self, dry_run: bool):
        """Delete inactive users who have not logged in in x months.
        email is unique and not nullable, therefore it's replaced with the object id."""

        expiry_date = timezone.now() - relativedelta(months=settings.INACTIVE_USER_TIMEOUT_IN_MONTHS)

        # retrieve inactive users who haven't logged in a month or more after receiving a warning
        last_month = timezone.now() - relativedelta(months=settings.INACTIVE_USER_WARNING_DELAY_IN_MONTHS)
        inactive_users_qs = self.get_users_with_last_action(expiry_date).filter(
            pending_deletion_notice_date__lte=last_month,
        )

        # remove inactive users
        if dry_run:
            self.stdout.write(
                f"Dry-run: suppression des utilisateurs: {inactive_users_qs.count()} auraient été supprimés"
            )
        else:
            deleted = secure_delete(
                inactive_users_qs,
                [
                    "conversations.Conversation",  # ForeignKey to User
                    "conversations.TemplateTransactionalSendLog",  # Reverse Generic relation on User
                    "favorites.FavoriteList",  # ForeignKey to User
                    "favorites.FavoriteItem",  # ForeignKey to FavoriteList
                    "siaes.SiaeUser",  # ForeignKey to User
                    "siaes.SiaeUserRequest",  # ForeignKey to User (initiator and assignee)
                    "users.User",
                    "users.User_groups",  # ManyToManyField to User
                    "notes.Note",  # GenericForeignKey to User
                ],
            )

            log = f"Suppression des utilisateurs: {deleted.get('users.User', 0)} ont été supprimés"
            if deleted:
                log += f" ({deleted})"
            self.stdout.write(log)

    @transaction.atomic
    def anonymize_stats(self, dry_run: bool):
        """Wipe personal data from StatsUser objects linked to deleted users"""

        stats = StatsUser.objects.exclude(id__in=User.objects.values_list("id", flat=True)).filter(anonymized_at=None)

        if dry_run:
            self.stdout.write(f"Dry-run: anonymisation des stats: {stats.count()} auraient été anonymisées")
            return

        anon_stats = stats.update(
            email="", first_name="", last_name="", phone="", company_name="", anonymized_at=timezone.now()
        )
        self.stdout.write(f"Anonymisation des stats: {anon_stats} ont été anonymisées")
