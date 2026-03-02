from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(years=3)
        qs = User.objects.filter(last_login__lte=expiry_date)
        users_to_delete_count = qs.count()
        qs.delete()
        self.stdout.write(f"Utilisateurs supprimés avec succès ({users_to_delete_count} traités)")
