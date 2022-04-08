from django.test import TestCase

from lemarche.networks.models import Network
from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeGroup, SiaeLabel, SiaeOffer, SiaeUser
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.models import User


class FixturesTest(TestCase):
    fixtures = [
        "lemarche/fixtures/django/01_siaegroups.json",
        "lemarche/fixtures/django/01_siaes.json",
        "lemarche/fixtures/django/02_users.json",
        "lemarche/fixtures/django/03_siae_users.json",
        "lemarche/fixtures/django/04_sectorgroups.json",
        "lemarche/fixtures/django/05_sectors.json",
        "lemarche/fixtures/django/06_siae_sectors.json",
        "lemarche/fixtures/django/06_siaegroup_sectors.json",
        "lemarche/fixtures/django/07_networks.json",
        "lemarche/fixtures/django/08_siae_networks.json",
        "lemarche/fixtures/django/09_siaeclientreferences.json",
        "lemarche/fixtures/django/09_siaelabels.json",
        "lemarche/fixtures/django/09_siaeoffers.json",
        "lemarche/fixtures/django/10_tenders.json",
        "lemarche/fixtures/django/11_tender_sectors.json",
        "lemarche/fixtures/django/11_tender_siaes.json",
        "lemarche/fixtures/django/20_cms.json",
    ]

    def test_flat_fixtures_load_successfully(self):
        # alternative?
        # management.call_command("loaddata", "lemarche/fixtures/django/01_siaes.json")
        # why not self.assertTrue(Siae.objects.all().count()) ?
        # returns an error: django.db.utils.InternalError: variable not found in subplan target list
        self.assertTrue(len(Siae.objects.all()) > 0)
        self.assertTrue(len(SiaeGroup.objects.all()) > 0)
        self.assertTrue(len(User.objects.all()) > 0)
        self.assertTrue(len(SiaeUser.objects.all()) > 0)
        self.assertTrue(len(Sector.objects.all()) > 0)
        self.assertTrue(len(SectorGroup.objects.all()) > 0)
        self.assertTrue(len(Network.objects.all()) > 0)
        self.assertTrue(len(SiaeClientReference.objects.all()) > 0)
        self.assertTrue(len(SiaeLabel.objects.all()) > 0)
        self.assertTrue(len(SiaeOffer.objects.all()) > 0)
        self.assertTrue(len(Tender.objects.all()) > 0)
        self.assertTrue(len(TenderSiae.objects.all()) > 0)
