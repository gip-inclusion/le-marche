from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import GEO_RANGE_CUSTOM
from lemarche.tenders.factories import TenderFactory
from lemarche.www.tenders.tasks import find_opportunities_for_siaes


class TenderMatchingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sectors = [SectorFactory() for i in range(10)]
        cls.perimeter_one = PerimeterFactory()
        cls.perimeter_two = PerimeterFactory()
        siae_one = SiaeFactory(is_active=True, geo_range=GEO_RANGE_CUSTOM)
        siae_two = SiaeFactory(is_active=True, geo_range=GEO_RANGE_CUSTOM)
        for i in range(5):
            siae_one.sectors.add(cls.sectors[i])
            siae_two.sectors.add(cls.sectors[i + 5])

    def test_matching_tenders_siae(self):
        tender = TenderFactory(sectors=self.sectors)
        siaes = find_opportunities_for_siaes(tender)
        # all_siaes = Siae.objects.all()
        # import ipdb

        # ipdb.set_trace()
        self.assertEqual(len(siaes.get()), 2)
