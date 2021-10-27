from django.core import management
from django.test import TestCase

from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes.models import Siae, SiaeUser
from lemarche.users.models import User


class FixturesTest(TestCase):
    def test_flat_fixtures_load_successfully(self):
        management.call_command("loaddata", "lemarche/fixtures/django/01_siaes.json")
        management.call_command("loaddata", "lemarche/fixtures/django/02_users.json")
        management.call_command("loaddata", "lemarche/fixtures/django/03_siae_users.json")
        management.call_command("loaddata", "lemarche/fixtures/django/04_sectors.json")
        management.call_command("loaddata", "lemarche/fixtures/django/05_siae_sectors.json")
        self.assertTrue(Siae.objects.count())
        self.assertTrue(User.objects.count())
        self.assertTrue(SiaeUser.objects.count())
        self.assertTrue(Sector.objects.count())
        self.assertTrue(SectorGroup.objects.count())
