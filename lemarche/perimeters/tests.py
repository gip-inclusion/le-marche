from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter


class PerimeterModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        cls.perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.perimeter_department_2 = PerimeterFactory(
            name="Guadeloupe", kind=Perimeter.KIND_DEPARTMENT, insee_code="971", region_code="01"
        )
        cls.perimeter_region = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        cls.perimeter_region_2 = PerimeterFactory(name="Guadeloupe", kind=Perimeter.KIND_REGION, insee_code="R01")

    def test_slug_field(self):
        self.assertEqual(self.perimeter_city.slug, "grenoble-38")
        self.assertEqual(self.perimeter_department.slug, "isere")
        self.assertEqual(self.perimeter_department_2.slug, "guadeloupe")
        self.assertEqual(self.perimeter_region.slug, "auvergne-rhone-alpes-region")
        self.assertEqual(self.perimeter_region_2.slug, "guadeloupe-region")

    def test_name_display_property(self):
        self.assertEqual(str(self.perimeter_city), "Grenoble (38)")
        self.assertEqual(str(self.perimeter_department), "Isère")
        self.assertEqual(str(self.perimeter_region), "Auvergne-Rhône-Alpes")


class PerimeterQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        cls.perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.perimeter_department_2 = PerimeterFactory(
            name="Guadeloupe", kind=Perimeter.KIND_DEPARTMENT, insee_code="971", region_code="01"
        )
        cls.perimeter_region = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        cls.perimeter_region_2 = PerimeterFactory(name="Guadeloupe", kind=Perimeter.KIND_REGION, insee_code="R01")

    def test_cities(self):
        self.assertEqual(Perimeter.objects.count(), 5)
        qs = Perimeter.objects.cities()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), self.perimeter_city)

    def test_regions(self):
        self.assertEqual(Perimeter.objects.count(), 5)
        qs = Perimeter.objects.regions()
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs.first(), self.perimeter_region)

    def test_name_search(self):
        qs = Perimeter.objects.name_search("Grenoble")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), self.perimeter_city)
        qs = Perimeter.objects.name_search("guadelou")
        self.assertEqual(qs.count(), 2)

    def test_post_code_search(self):
        qs = Perimeter.objects.post_code_search("38000")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), self.perimeter_city)
        qs = Perimeter.objects.post_code_search("38")
        self.assertEqual(qs.count(), 2)
