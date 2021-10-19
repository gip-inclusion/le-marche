from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter


class PerimeterModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble", kind=Perimeter.KIND_CITY, insee_code="38185", department_code="38", region_code="84"
        )
        cls.perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.perimeter_region = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )

    def test_name_display_property(self):
        self.assertEqual(str(self.perimeter_city), "Grenoble (38)")
        self.assertEqual(str(self.perimeter_department), "Isère")
        self.assertEqual(str(self.perimeter_region), "Auvergne-Rhône-Alpes")
