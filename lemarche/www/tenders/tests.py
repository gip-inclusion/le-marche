from django.contrib.gis.geos import Point
from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import GEO_RANGE_COUNTRY, GEO_RANGE_CUSTOM, GEO_RANGE_DEPARTMENT
from lemarche.tenders.factories import TenderFactory
from lemarche.www.tenders.tasks import find_opportunities_for_siaes


class TenderMatchingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sectors = [SectorFactory() for i in range(10)]
        cls.perimeters = [PerimeterFactory(department_code="75"), PerimeterFactory()]
        # by default is Paris
        coords_paris = Point(48.86385199985207, 2.337071483848432)

        siae_one = SiaeFactory(
            is_active=True, geo_range=GEO_RANGE_CUSTOM, coords=coords_paris, geo_range_custom_distance=100
        )
        siae_two = SiaeFactory(
            is_active=True, geo_range=GEO_RANGE_CUSTOM, coords=coords_paris, geo_range_custom_distance=10
        )
        for i in range(5):
            siae_one.sectors.add(cls.sectors[i])
            siae_two.sectors.add(cls.sectors[i + 5])

    def test_matching_tenders_siae(self):
        tender = TenderFactory(sectors=self.sectors)
        siaes = find_opportunities_for_siaes(tender)
        self.assertEqual(len(siaes.get()), 2)

    def test_with_siae_country(self):
        # add Siae with geo_range_country
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_country = SiaeFactory(is_active=True, geo_range=GEO_RANGE_COUNTRY)
        siae_country.sectors.add(self.sectors[0])
        siaes = find_opportunities_for_siaes(tender)
        self.assertEqual(len(siaes.get()), 3)

    def test_with_siae_department(self):
        # add Siae with geo_range_country
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_department = SiaeFactory(is_active=True, department="75", geo_range=GEO_RANGE_DEPARTMENT)
        siae_department.sectors.add(self.sectors[0])
        siaes = find_opportunities_for_siaes(tender)
        self.assertEqual(len(siaes.get()), 3)

    def test_no_siaes(self):
        tender = TenderFactory(sectors=[SectorFactory()], perimeters=self.perimeters)
        siaes = find_opportunities_for_siaes(tender)
        self.assertEqual(len(siaes.get()), 0)
        tender_marseille = TenderFactory(
            sectors=self.sectors, perimeters=[PerimeterFactory(coords=Point(43.35101634452076, 5.379616625955892))]
        )
        siaes_marseille = find_opportunities_for_siaes(tender_marseille)
        self.assertEqual(len(siaes_marseille.get()), 0)
        siae = SiaeFactory(is_active=True, department="75", geo_range=GEO_RANGE_COUNTRY)
        siaes_marseille = find_opportunities_for_siaes(tender_marseille)
        self.assertEqual(len(siaes_marseille.get()), 0)
        # add sector
        siae.sectors.add(self.sectors[0])
        siaes_marseille = find_opportunities_for_siaes(tender_marseille)
        self.assertEqual(len(siaes_marseille.get()), 1)

    def test_with_no_contact_email(self):
        # test when siae doesn't have contact email
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_country = SiaeFactory(is_active=True, geo_range=GEO_RANGE_COUNTRY, contact_email="")
        siae_country.sectors.add(self.sectors[0])
        siaes = find_opportunities_for_siaes(tender)
        self.assertEqual(len(siaes.get()), 2)

    # def test_number_queries(self):
    #     tender = TenderFactory(sectors=self.sectors)
    #     with self.assertNumQueries(8):
    #         siaes = find_opportunities_for_siaes(tender)
    #     self.assertEqual(len(siaes.get()), 2)
