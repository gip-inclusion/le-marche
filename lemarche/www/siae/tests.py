from django.contrib.gis.geos import Point
from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.www.siae.forms import SiaeSearchForm


class SiaeSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            coords=Point(5.7301, 45.1825),
        )
        PerimeterFactory(name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84")
        PerimeterFactory(name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84")
        SiaeFactory(city="Grenoble", department="38", region="Auvergne-Rhône-Alpes", geo_range=Siae.GEO_RANGE_COUNTRY)
        SiaeFactory(city="Grenoble", department="38", region="Auvergne-Rhône-Alpes", geo_range=Siae.GEO_RANGE_REGION)
        SiaeFactory(
            city="Grenoble", department="38", region="Auvergne-Rhône-Alpes", geo_range=Siae.GEO_RANGE_DEPARTMENT
        )
        SiaeFactory(
            city="Grenoble",
            department="38",
            region="Auvergne-Rhône-Alpes",
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(5.7301, 45.1825),
        )
        SiaeFactory(city="Lyon", department="69", region="Auvergne-Rhône-Alpes", geo_range=Siae.GEO_RANGE_COUNTRY)
        SiaeFactory(city="Lyon", department="69", region="Auvergne-Rhône-Alpes", geo_range=Siae.GEO_RANGE_REGION)
        SiaeFactory(city="Lyon", department="69", region="Auvergne-Rhône-Alpes", geo_range=Siae.GEO_RANGE_DEPARTMENT)
        SiaeFactory(
            city="Lyon",
            department="69",
            region="Auvergne-Rhône-Alpes",
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(4.8236, 45.7685),
        )
        SiaeFactory(city="Quimper", department="29", region="Bretagne", geo_range=Siae.GEO_RANGE_COUNTRY)
        SiaeFactory(city="Quimper", department="29", region="Bretagne", geo_range=Siae.GEO_RANGE_REGION)
        SiaeFactory(city="Quimper", department="29", region="Bretagne", geo_range=Siae.GEO_RANGE_DEPARTMENT)
        SiaeFactory(
            city="Quimper",
            department="29",
            region="Bretagne",
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(-4.0916, 47.9914),
        )

    def test_search_perimeter_none(self):
        form = SiaeSearchForm({"perimeter": ""})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 12)

    def test_search_perimeter_region(self):
        form = SiaeSearchForm({"perimeter": "auvergne-rhone-alpes"})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 8)

    def test_search_perimeter_department(self):
        form = SiaeSearchForm({"perimeter": "isere"})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 4)

    def test_search_perimeter_city(self):
        form = SiaeSearchForm({"perimeter": "grenoble-38"})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 1)
