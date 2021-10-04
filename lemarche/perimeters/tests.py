from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter


class PerimeterModelTest(TestCase):
    def setUp(self):
        pass

    def test_display_name(self):
        perimeter_city = PerimeterFactory(
            name="Grenoble", kind=Perimeter.KIND_CITY, insee_code="38185", department_code="38", region_code="84"
        )
        self.assertEqual(str(perimeter_city), "Grenoble (38)")
        perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        self.assertEqual(str(perimeter_department), "Isère")
        perimeter_region = PerimeterFactory(name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84")
        self.assertEqual(str(perimeter_region), "Auvergne-Rhône-Alpes")
