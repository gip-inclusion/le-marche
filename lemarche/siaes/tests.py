from django.test import TestCase

from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory


class SiaeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        siae = SiaeFactory(name="Ma boite")
        self.assertEqual(str(siae), "Ma boite")

    def test_is_live_queryset(self):
        SiaeFactory(is_active=True, is_delisted=True)
        SiaeFactory(is_active=False, is_delisted=True)
        SiaeFactory(is_active=True, is_delisted=False)  # live
        SiaeFactory(is_active=False, is_delisted=False)
        self.assertEqual(Siae.objects.count(), 4)
        self.assertEqual(Siae.objects.is_live().count(), 1)
        self.assertEqual(Siae.objects.is_not_live().count(), 3)

    def test_has_user_queryset(self):
        SiaeFactory()
        siae = SiaeFactory()
        user = UserFactory()
        siae.users.add(user)
        self.assertEqual(Siae.objects.count(), 2)
        self.assertEqual(Siae.objects.has_user().count(), 1)

    def test_geo_range_pretty_display_property(self):
        siae_country = SiaeFactory(geo_range=Siae.GEO_RANGE_COUNTRY)
        self.assertEqual(siae_country.geo_range_pretty_display, "France entière")
        siae_region = SiaeFactory(geo_range=Siae.GEO_RANGE_REGION, region="Guadeloupe")
        self.assertEqual(siae_region.geo_range_pretty_display, "région (Guadeloupe)")
        siae_department = SiaeFactory(geo_range=Siae.GEO_RANGE_DEPARTMENT, region="Bretagne", department="29")
        self.assertEqual(siae_department.geo_range_pretty_display, "département (29)")
        siae_custom = SiaeFactory(
            geo_range=Siae.GEO_RANGE_CUSTOM,
            region="Bretagne",
            department="29",
            city="Quimper",
            geo_range_custom_distance=50,
        )
        self.assertEqual(siae_custom.geo_range_pretty_display, "50 km")
        siae_custom_empty = SiaeFactory(
            geo_range=Siae.GEO_RANGE_CUSTOM, region="Bretagne", department="29", city="Quimper"
        )
        self.assertEqual(siae_custom_empty.geo_range_pretty_display, "non disponible")
