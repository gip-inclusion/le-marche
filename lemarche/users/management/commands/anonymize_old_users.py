from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.postgres.functions import RandomUUID
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Concat
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
            self.anonymize_old_users(expiry_date=expiry_date, dry_run=options["dry_run"])
        except DryRunException:
            self.stdout.write("Fin du dry_run d'anonymisation")

        self.warn_users_by_email(expiry_date=expiry_date, warning_date=warning_date, dry_run=options["dry_run"])

    @transaction.atomic
    def anonymize_old_users(self, expiry_date: timezone.datetime, dry_run: bool):
        """Update inactive users since x months and strip them from their personal data.
        email is unique and not nullable, therefore it's replaced with the object id."""

        qs = User.objects.filter(last_login__lte=expiry_date, is_anonymized=False)
        users_to_update_count = qs.count()

        qs.update(
            is_active=False,  # inactive users are allowed to log in standard login views
            is_anonymized=True,
            email=Concat(F("id"), Value("@domain.invalid")),
            first_name="",
            last_name="",
            phone="",
            api_key=None,
            api_key_last_updated=None,
            # https://docs.djangoproject.com/en/5.1/ref/contrib/auth/#django.contrib.auth.models.User.set_unusable_password
            # Imitating the method but in sql. Prevent password reset attempt
            # Random string is to avoid chances of impersonation by admins https://code.djangoproject.com/ticket/20079
            password=Concat(Value(UNUSABLE_PASSWORD_PREFIX), RandomUUID()),
        )
        # remove anonymized users in Siaes
        SiaeUser.objects.filter(user__is_anonymized=True).delete()

        self.stdout.write(f"Utilisateurs anonymisés avec succès ({users_to_update_count} traités)")

        if dry_run:  # cancel transaction
            raise DryRunException

    @transaction.atomic
    def warn_users_by_email(self, warning_date: timezone.datetime, expiry_date: timezone.datetime, dry_run: bool):
        email_template = TemplateTransactional.objects.get(code="USER_ANONYMIZATION_WARNING")

        # Users that have already received the mail are excluded
        users_to_warn = User.objects.filter(last_login__lte=warning_date, is_active=True, is_anonymized=False).exclude(
            recipient_transactional_send_logs__template_transactional__code=email_template.code
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
                    "anonymization_date": defaulttags.date(expiry_date),  # natural date
                },
                recipient_content_object=user,
            )

        self.stdout.write(f"Un email d'avertissement a été envoyé à {users_to_warn.count()} utilisateurs")
