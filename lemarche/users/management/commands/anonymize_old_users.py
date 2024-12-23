from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.postgres.functions import RandomUUID

from dateutil.relativedelta import relativedelta

from lemarche.users.models import User


class Command(BaseCommand):
    """Update and anonymize inactive users past a defined inactivity period"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--month_timeout",
            type=int,
            default=12,  # todo define a constant, but where ? base.py ?
            help="Délai en mois à partir duquel les utilisateurs sont considérés inactifs",
        )

    def handle(self, *args, **options):
        """Update inactive users since x months and strip them from their personal data
        email cannot be deleted, so it is replaced by a concatenation of the User id
        and a fake domain name"""
        expiry_date = timezone.now() - relativedelta(months=options["month_timeout"])

        with transaction.atomic():
            User.objects.filter(last_login__lt=expiry_date).update(
                is_active=False,  # inactive users should not be allowed to log in
                email=Concat(F("id"), Value("@inactive.com")),
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
