from lemarche.stats.models import StatsUser
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template import defaulttags
from django.utils import timezone

from lemarche.conversations.models import TemplateTransactional
from lemarche.siaes.models import SiaeUser
from lemarche.users.models import User


class DryRunException(Exception):
    """To be raised in a dry run mode to abort current transaction"""

    pass


class Command(BaseCommand):
    """Update and anonymize inactive users past a defined inactivity period"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--month_timeout",
            type=int,
            default=settings.INACTIVE_USER_TIMEOUT_IN_MONTHS,
            help="Délai en mois à partir duquel les utilisateurs sont considérés inactifs",
        )
        parser.add_argument(
            "--warning_delay",
            type=int,
            default=settings.INACTIVE_USER_WARNING_DELAY_IN_DAYS,
            help="Délai en jours avant la date de suppression pour prevenir les utilisateurs",
        )
        parser.add_argument(
            "--dry_run",
            type=bool,
            default=False,
            help="La commande est exécutée sans que les modifications soient transmises à la base",
        )

    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(months=options["month_timeout"])
        warning_date = expiry_date + relativedelta(days=options["warning_delay"])

        try:
            self.delete_old_users(expiry_date=expiry_date, dry_run=options["dry_run"])
        except DryRunException:
            self.stdout.write("Fin du dry_run d'anonymisation")

        self.warn_users_by_email(expiry_date=expiry_date, warning_date=warning_date, dry_run=options["dry_run"])

    @transaction.atomic
    def delete_old_users(self, expiry_date: timezone.datetime, dry_run: bool):
        """Delete inactive users who have not logged in in x months.
        email is unique and not nullable, therefore it's replaced with the object id."""

        qs = User.objects.filter(last_login__lte=expiry_date, is_anonymized=False)
        users_to_delete_count = qs.count()

        # wipe personal data from related StatsUser objects
        # emails = qs.values_list("email", flat=True)
        # stats = StatsUser.objects.filter(email__in=emails)
        # stats.anonymize_update()

        # remove inactive users
        qs.delete()

        # remove anonymized users in Siaes
        # SiaeUser.objects.filter(user__is_anonymized=True).delete()

        self.stdout.write(f"Utilisateurs supprimés avec succès ({users_to_delete_count} traités)")

        if dry_run:  # cancel transaction
            raise DryRunException

    @transaction.atomic
    def warn_users_by_email(self, warning_date: timezone.datetime, expiry_date: timezone.datetime, dry_run: bool):
        email_template = TemplateTransactional.objects.get(code="USER_DELETION_WARNING")

        # Users that have already received the mail are excluded
        users_to_warn = User.objects.filter(last_login__lte=warning_date, is_active=True, is_anonymized=False).exclude(
            recipient_transactional_send_logs__template_transactional__code=email_template.code,
            recipient_transactional_send_logs__extra_data__contains={"sent": True},
        )

        if dry_run:
            self.stdout.write(
                f"Fin du dry_run d'avertissement des utilisateurs, {users_to_warn.count()} auraient été avertis"
            )
            return  # exit before sending emails

        for user in users_to_warn:
            email_template.send_transactional_email(
                recipient_email=user.email,
                recipient_name=user.full_name,
                variables={
                    "user_full_name": user.full_name,
                    "deletion_date": defaulttags.date(expiry_date),  # natural date
                },
                recipient_content_object=user,
            )

        self.stdout.write(f"Un email d'avertissement a été envoyé à {users_to_warn.count()} utilisateurs")
