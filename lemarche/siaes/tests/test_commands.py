from django.core.management import call_command
from django.test import TransactionTestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import SiaeActivity


class SiaeActivitiesCreateCommandTest(TransactionTestCase):
    def setUp(self):
        self.sector1 = SectorFactory()
        self.sector2 = SectorFactory()
        self.sector3 = SectorFactory()

        self.region_name = "Collectivités d'outre-mer"

        self.perimeter_department = PerimeterFactory(
            name="Saint-Martin", kind=Perimeter.KIND_DEPARTMENT, insee_code="978", region_code="97"
        )
        self.perimeter_region = PerimeterFactory(name=self.region_name, kind=Perimeter.KIND_REGION, insee_code="R97")

    def test_create_activities_failed_with_department(self):
        # Siae with department geo_range but no department
        siae = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_EA,
            presta_type=[siae_constants.PRESTA_DISP],
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
        )
        siae.sectors.set([self.sector2, self.sector3])

        with self.assertRaises(Perimeter.DoesNotExist):
            call_command("create_siae_activities")

        siae.is_delisted = True
        siae.save()
        call_command("create_siae_activities")
        self.assertEqual(SiaeActivity.objects.count(), 0)

    def test_create_activities_failed_with_region(self):
        # Siae with region geo_range but no region
        siae = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_EA,
            presta_type=[siae_constants.PRESTA_DISP],
            geo_range=siae_constants.GEO_RANGE_REGION,
        )
        siae.sectors.set([self.sector2, self.sector3])

        with self.assertRaises(Perimeter.DoesNotExist):
            call_command("create_siae_activities")

        siae.is_delisted = True
        siae.save()
        call_command("create_siae_activities")
        self.assertEqual(SiaeActivity.objects.count(), 0)

    def test_create_activities(self):
        siae1 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            geo_range=siae_constants.GEO_RANGE_COUNTRY,
        )
        siae1.sectors.set([self.sector1, self.sector2])

        siae2 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_EA,
            presta_type=[siae_constants.PRESTA_DISP],
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
        )
        siae2.sectors.set([self.sector3])

        siae3 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_EA,
            presta_type=[siae_constants.PRESTA_PREST],
            geo_range=siae_constants.GEO_RANGE_REGION,
            department="987",
            region=self.region_name,
        )
        siae3.sectors.set([self.sector3])

        siae4 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_EA,
            presta_type=[siae_constants.PRESTA_DISP],
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
            department="978",
            region=self.region_name,
        )
        siae4.sectors.set([self.sector2, self.sector3])

        call_command("create_siae_activities", dry_run=True)
        self.assertEqual(SiaeActivity.objects.count(), 0)

        call_command("create_siae_activities")
        self.assertEqual(SiaeActivity.objects.count(), 2 + 1 + 1 + 2)
        siae1_activities = SiaeActivity.objects.filter(siae=siae1)
        self.assertEqual(siae1_activities.count(), 2)
        self.assertEqual(siae1_activities.filter(sectors__in=[self.sector1]).count(), 1)
        self.assertEqual(siae1_activities.filter(sectors__in=[self.sector2]).count(), 1)
        for siae_activity in siae1_activities:
            with self.subTest(siae_activity=siae_activity):
                self.assertEqual(siae_activity.presta_type, [siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD])
                self.assertEqual(siae_activity.geo_range, siae_constants.GEO_RANGE_COUNTRY)
                self.assertEqual(siae_activity.locations.count(), 0)

        siae2_activities = SiaeActivity.objects.filter(siae=siae2)
        self.assertEqual(siae2_activities.count(), 1)
        self.assertEqual(siae2_activities.first().presta_type, [siae_constants.PRESTA_DISP])
        self.assertEqual(siae2_activities.first().geo_range, siae_constants.GEO_RANGE_CUSTOM)
        self.assertEqual(siae2_activities.first().geo_range_custom_distance, siae2.geo_range_custom_distance)
        self.assertEqual(siae2_activities.filter(sectors__in=[self.sector3]).count(), 1)
        self.assertEqual(siae2_activities.first().locations.count(), 0)

        siae3_activities = SiaeActivity.objects.filter(siae=siae3)
        self.assertEqual(siae3_activities.count(), 1)
        self.assertEqual(siae3_activities.filter(sectors__in=[self.sector3]).count(), 1)
        self.assertEqual(siae3_activities.first().presta_type, [siae_constants.PRESTA_PREST])
        self.assertEqual(siae3_activities.first().geo_range, siae_constants.GEO_RANGE_ZONES)
        self.assertEqual(siae3_activities.first().locations.count(), 1)
        self.assertEqual(siae3_activities.first().locations.first(), self.perimeter_region)

        siae4_activities = SiaeActivity.objects.filter(siae=siae4)
        self.assertEqual(siae4_activities.count(), 2)
        self.assertEqual(siae4_activities.filter(sectors__in=[self.sector2]).count(), 1)
        self.assertEqual(siae4_activities.filter(sectors__in=[self.sector3]).count(), 1)
        for siae_activity in siae4_activities:
            with self.subTest(siae_activity=siae_activity):
                self.assertEqual(siae_activity.presta_type, [siae_constants.PRESTA_DISP])
                self.assertEqual(siae_activity.geo_range, siae_constants.GEO_RANGE_ZONES)
                self.assertEqual(siae_activity.locations.count(), 1)
                self.assertEqual(siae_activity.locations.first(), self.perimeter_department)