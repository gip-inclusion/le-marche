from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.postgres.functions import RandomUUID
from django.conf import settings
from django.template import defaulttags

from dateutil.relativedelta import relativedelta

from lemarche.conversations.models import TemplateTransactional
from lemarche.users.models import User


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

    def handle(self, *args, **options):
        """Update inactive users since x months and strip them from their personal data
        email is unique and not nullable, therefore it's replaced with the object id."""
        expiry_date = timezone.now() - relativedelta(months=options["month_timeout"])
        warning_date = expiry_date + relativedelta(days=options["warning_delay"])

        with (
            transaction.atomic()
        ):  # fixme tester a ne pas anonymiser a chaque fois (mettre un flag) on supprime aussi les admins ect ??
            User.objects.filter(last_login__lte=expiry_date).update(
                is_active=False,  # inactive users are allowed to log in standard login views
                email=F("id"),
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

            self.stdout.write("Utilisateurs anonymisés avec succès")

        email_template = TemplateTransactional.objects.get(code="USER_ANONYMIZATION_WARNING")

        with transaction.atomic():
            # Users that have already received the mail are excluded
            users_to_warn = User.objects.filter(last_login__lte=warning_date, is_active=True).exclude(
                recipient_transactional_send_logs__template_transactional__code=email_template.code
            )
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
