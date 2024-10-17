from django.contrib.gis.geos import Point
from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.siaes.models import Siae, SiaeActivity
from lemarche.tenders.factories import TenderFactory


class TenderMatchingActivitiesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sectors = [SectorFactory() for i in range(10)]
        cls.other_sector = SectorFactory()
        cls.perimeter_paris = PerimeterFactory(department_code="75", post_codes=["75019", "75018"])
        cls.perimeter_marseille = PerimeterFactory(coords=Point(43.35101634452076, 5.379616625955892))
        cls.perimeters = [cls.perimeter_paris, PerimeterFactory()]
        # by default is Paris
        coords_paris = Point(48.86385199985207, 2.337071483848432)

        cls.siae_one = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            coords=coords_paris,
        )
        cls.siae_one_activity = SiaeActivityFactory(
            siae=cls.siae_one,
            sector_group=cls.sectors[0].group,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=100,
        )
        cls.siae_one_activity.locations.set([cls.perimeter_paris])
        cls.siae_one_other_activity = SiaeActivityFactory(
            siae=cls.siae_one,
            sector_group=cls.other_sector.group,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )
        cls.siae_one_other_activity.sectors.add(cls.other_sector)

        cls.siae_two = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_ESAT,
            coords=coords_paris,
        )
        cls.siae_two_activity = SiaeActivityFactory(
            siae=cls.siae_two,
            sector_group=cls.sectors[5].group,
            presta_type=[siae_constants.PRESTA_BUILD],
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
        )

        for i in range(5):
            cls.siae_one_activity.sectors.add(cls.sectors[i])
            cls.siae_two_activity.sectors.add(cls.sectors[i + 5])

        cls.siae_three = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_ESAT,
            coords=Point(46.15926, -1.15099),  # La Rochelle
        )
        cls.siae_three_activity = SiaeActivityFactory(
            siae=cls.siae_three,
            sector_group=cls.other_sector.group,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )
        cls.siae_three_activity.sectors.add(cls.other_sector)

    def test_matching_siae_presta_type(self):
        tender = TenderFactory(presta_type=[], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD], sectors=self.sectors, perimeters=self.perimeters
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(
            presta_type=[siae_constants.PRESTA_PREST], sectors=self.sectors, perimeters=self.perimeters
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 1)

    def test_matching_siae_kind(self):
        tender = TenderFactory(siae_kind=[], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(siae_kind=[siae_constants.KIND_AI], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 1)
        tender = TenderFactory(
            siae_kind=[siae_constants.KIND_ESAT, siae_constants.KIND_AI],
            sectors=self.sectors,
            perimeters=self.perimeters,
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(siae_kind=[siae_constants.KIND_SEP], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 0)

    def test_matching_siae_sectors(self):
        tender = TenderFactory(sectors=self.sectors)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)

    def test_matching_siae_distance_location(self):
        # create SIAE in Tours
        siae_tours = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            coords=Point(47.392287, 0.690049),  # Tours city
        )
        siae_tours_activity = SiaeActivityFactory(
            siae=siae_tours,
            sector_group=self.sectors[0].group,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_custom_distance_perimeter=True,
        )

        siae_tours_activity.sectors.add(self.sectors[0])

        # create SIAE in Marseille
        siae_marseille = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            coords=self.perimeter_marseille.coords,
        )
        siae_marseille_activity = SiaeActivityFactory(
            siae=siae_marseille,
            sector_group=self.sectors[0].group,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )
        siae_marseille_activity.sectors.add(self.sectors[0])

        # create tender in Azay-le-rideau (near Tours ~25km)
        perimeter_azaylerideau = PerimeterFactory(coords=Point(47.262352, 0.466372))
        tender = TenderFactory(
            location=perimeter_azaylerideau,
            distance_location=30,
            siae_kind=[siae_constants.KIND_ESAT, siae_constants.KIND_AI],
            sectors=self.sectors,
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 1)
        self.assertIn(siae_tours, siae_found_list)

        # Azay-le-rideau is less than 240km from Paris but more 550km from Marseille
        tender = TenderFactory(
            location=perimeter_azaylerideau,
            distance_location=300,
            siae_kind=[siae_constants.KIND_ESAT, siae_constants.KIND_AI],
            sectors=self.sectors,
            perimeters=[self.perimeter_paris],  # test this option without effect when the distance is setted
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        # self.assertEqual(len(siae_found_list), 3)
        self.assertIn(siae_tours, siae_found_list)
        self.assertIn(self.siae_one, siae_found_list)
        self.assertIn(self.siae_two, siae_found_list)

        # unset distance location, perimeters is used instead, Paris as it happens
        tender.distance_location = None
        tender.save()
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)
        self.assertIn(self.siae_one, siae_found_list)
        self.assertIn(self.siae_two, siae_found_list)

        # set distance location and include country
        tender = TenderFactory(
            location=perimeter_azaylerideau,
            distance_location=50,
            siae_kind=[siae_constants.KIND_ESAT, siae_constants.KIND_AI],
            sectors=self.sectors,
            include_country_area=True,
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2)
        self.assertIn(siae_tours, siae_found_list)
        self.assertIn(siae_marseille, siae_found_list)

        # set a department in location disable distance_location, perimeters is used instead
        tender = TenderFactory(
            location=PerimeterFactory(
                name="Indre-et-loire", kind=Perimeter.KIND_DEPARTMENT, insee_code="37", region_code="24"
            ),
            distance_location=50,
            siae_kind=[siae_constants.KIND_ESAT, siae_constants.KIND_AI],
            sectors=self.sectors,
            include_country_area=True,  # check this option without effect when the distance is setted
            perimeters=[self.perimeter_paris],  # without effect too
        )
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 3)
        self.assertIn(self.siae_one, siae_found_list)
        self.assertIn(self.siae_two, siae_found_list)
        self.assertIn(siae_marseille, siae_found_list)

    def test_matching_siae_perimeters_custom(self):
        # add Siae with geo_range_country
        siae_country = SiaeFactory(is_active=True)
        siae_country_activity = SiaeActivityFactory(
            siae=siae_country,
            sector_group=self.sectors[0].group,
            presta_type=[],
            with_country_perimeter=True,
        )
        siae_country_activity.sectors.add(self.sectors[0])
        # tender perimeter custom with include_country_area = False
        tender_1 = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender_1)
        self.assertEqual(len(siae_found_list), 2 + 0)
        # tender perimeter custom with include_country_area = True
        tender_2 = TenderFactory(sectors=self.sectors, perimeters=self.perimeters, include_country_area=True)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender_2)
        self.assertEqual(len(siae_found_list), 2 + 1)

    def test_matching_siae_country(self):
        # add Siae with geo_range_country
        siae_country = SiaeFactory(is_active=True)
        siae_country_activity = SiaeActivityFactory(
            siae=siae_country,
            sector_group=self.sectors[0].group,
            with_country_perimeter=True,
        )
        siae_country_activity.sectors.add(self.sectors[0])

        siae_country_2 = SiaeFactory(is_active=True)
        siae_country_activity_2 = SiaeActivityFactory(
            siae=siae_country_2,
            sector_group=self.sectors[0].group,
            with_country_perimeter=True,
        )
        siae_country_activity_2.sectors.add(self.sectors[0])

        # tender perimeter custom with is_country_area = False
        tender_1 = TenderFactory(sectors=self.sectors, is_country_area=True)
        siae_found_list_1 = Siae.objects.filter_with_tender_through_activities(tender_1)
        self.assertEqual(len(siae_found_list_1), 2)
        # tender perimeter custom with include_country_area = True
        tender_2 = TenderFactory(sectors=self.sectors, include_country_area=True)
        siae_found_list_2 = Siae.objects.filter_with_tender_through_activities(tender_2)
        # we should have the same length of structures
        self.assertEqual(len(siae_found_list_1), len(siae_found_list_2))
        # add perimeters
        tender_2.perimeters.set(self.perimeters)
        siae_found_list_2 = Siae.objects.filter_with_tender_through_activities(tender_2)
        self.assertEqual(len(siae_found_list_2), 2 + 2)
        tender_2.is_country_area = True
        tender_2.save()
        siae_found_list_2 = Siae.objects.filter_with_tender_through_activities(tender_2)
        # we should have only siaes with country geo range
        self.assertEqual(len(siae_found_list_2), 2 + 0)

        # tender other sector perimeter custom with include_country_area = True
        tender_3 = TenderFactory(sectors=[self.other_sector], is_country_area=True)
        siae_found_list_3 = Siae.objects.filter_with_tender_through_activities(tender_3)
        self.assertEqual(len(siae_found_list_3), 2)
        self.assertIn(self.siae_one, siae_found_list_3)
        self.assertIn(self.siae_three, siae_found_list_3)
        tender_3.perimeters.set(self.perimeters)
        siae_found_list_3 = Siae.objects.filter_with_tender_through_activities(tender_3)
        self.assertEqual(len(siae_found_list_3), 2 + 0)  # other siae isn't in the same sector

    def test_matching_siae_perimeters_custom_2(self):
        # add Siae with geo_range_department (75)
        siae_department = SiaeFactory(is_active=True)
        siae_department_activity = SiaeActivityFactory(
            siae=siae_department, sector_group=self.sectors[0].group, with_zones_perimeter=True
        )
        siae_department_activity.sectors.add(self.sectors[0])
        perimeter_department = PerimeterFactory(
            name="Paris", kind=Perimeter.KIND_DEPARTMENT, insee_code="75", region_code="11"
        )
        siae_department_activity.locations.set([perimeter_department])

        # tender perimeter custom
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2 + 1)

    def test_matching_siae_perimeters_france(self):
        # tender france
        tender = TenderFactory(sectors=self.sectors, is_country_area=True)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 0)
        # add Siae with geo_range_country
        siae_country = SiaeFactory(is_active=True)
        siae_country_activity = SiaeActivityFactory(
            siae=siae_country, sector_group=self.sectors[0].group, with_country_perimeter=True
        )
        siae_country_activity.sectors.add(self.sectors[0])
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 1)

    def test_matching_siae_two_matching_activities(self):
        sector1 = SectorFactory()
        sector2 = SectorFactory()
        siae = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            coords=Point(48.86385199985207, 2.337071483848432),  # Paris
        )
        siae_activity1 = SiaeActivityFactory(
            siae=siae,
            sector_group=sector1.group,
            presta_type=[siae_constants.PRESTA_PREST],
            with_zones_perimeter=True,
        )
        siae_activity1.sectors.add(sector1)
        siae_activity1.locations.set([self.perimeter_paris])

        siae_activity2 = SiaeActivityFactory(
            siae=siae,
            sector_group=sector2.group,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_zones_perimeter=True,
        )
        siae_activity2.sectors.add(sector2)
        siae_activity2.locations.set([self.perimeter_paris])

        tender = TenderFactory(
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            sectors=[sector1, sector2],
            perimeters=[self.perimeter_paris],
        )

        activities_found_list = SiaeActivity.objects.filter_with_tender(tender)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(activities_found_list), 2)
        self.assertEqual(len(siae_found_list), 1)
        self.assertIn(siae, siae_found_list)

    def test_no_siaes(self):
        # tender with empty sectors list
        tender = TenderFactory(sectors=[SectorFactory()], perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 0)
        # tender near Marseille
        tender_marseille = TenderFactory(sectors=self.sectors, perimeters=[self.perimeter_marseille])
        siae_found_list_marseille = Siae.objects.filter_with_tender_through_activities(tender_marseille)
        self.assertEqual(len(siae_found_list_marseille), 0)

    def test_with_no_contact_email(self):
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae = SiaeFactory(is_active=True, contact_email="")
        siae_activity = SiaeActivityFactory(siae=siae, sector_group=self.sectors[0].group, with_zones_perimeter=True)
        siae_activity.locations.set([self.perimeter_paris])
        siae_activity.sectors.add(self.sectors[0])

        siae_found_list = Siae.objects.filter_with_tender_through_activities(tender)
        self.assertEqual(len(siae_found_list), 2 + 0)
        self.assertNotIn(siae, siae_found_list)
