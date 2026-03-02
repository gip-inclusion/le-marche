from django.db.models.query_utils import Q
from lemarche.stats.models import StatsUser
from lemarche.users.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        emails = User.objects.values_list("email", flat=True)
        stats = StatsUser.objects.filter(~Q(email__in=emails))
        stats.anonymize_update()
