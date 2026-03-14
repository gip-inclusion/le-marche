from datetime import UTC, datetime
from io import StringIO

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from lemarche.stats.models import Tracker
from tests.stats.factories import TrackerFactory


@freeze_time(datetime(year=2024, month=1, day=1, tzinfo=UTC))
class TrackerDeletionTestCase(TestCase):
    def test_delete_old_trackers(self):
        expiry_date = timezone.now() - relativedelta(years=3)
        recent_tracker = TrackerFactory()
        TrackerFactory(date_created=expiry_date)

        std_out = StringIO()
        call_command("delete_old_trackers", dry_run=True, stdout=std_out)
        self.assertEqual(Tracker.objects.count(), 2)
        assert std_out.getvalue() == "Dry-run: suppression des anciens trackers: 1 auraient été supprimés\n"

        std_out = StringIO()
        call_command("delete_old_trackers", dry_run=False, stdout=std_out)
        self.assertEqual(Tracker.objects.count(), 1)
        assert std_out.getvalue() == "Suppression des anciens trackers: 1 ont été supprimés ({'stats.Tracker': 1})\n"
        self.assertEqual(Tracker.objects.get(), recent_tracker)
