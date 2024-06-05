import freezegun
from django.core.management import call_command
from django.test import TestCase

from lemarche.analytics.models import Datum
from lemarche.siaes.factories import SiaeFactory


class AnalyticsTestCase(TestCase):
    @freezegun.freeze_time("2024-06-08", as_kwarg="frozen_time")
    def test_collect_data(self, frozen_time):
        siae = SiaeFactory(is_active=True, is_delisted=False, completion_rate=42.1)
        call_command("collect_analytics_data", save=True)

        datum = Datum.objects.get()
        self.assertEquals(datum.value, 42)

        frozen_time.move_to("2024-06-12")
        siae.completion_rate = 53.7
        siae.save()
        call_command("collect_analytics_data", save=True)

        datum = Datum.objects.last()
        self.assertEquals(datum.value, 53)
        all_datum_count = Datum.objects.all().count()
        self.assertEquals(all_datum_count, 2)
