from django.db.models import Avg

from lemarche.siaes.models import Siae


def collect_siae_analytics_data():
    return Siae.objects.is_live().aggregate(Avg("completion_rate"))
