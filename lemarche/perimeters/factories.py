import factory
from django.contrib.gis.geos import Point
from factory.django import DjangoModelFactory

from lemarche.perimeters.models import Perimeter


class PerimeterFactory(DjangoModelFactory):
    class Meta:
        model = Perimeter

    name = "Paris"
    # slug: auto-generated
    kind = Perimeter.KIND_CITY
    insee_code = factory.Sequence(lambda n: n)
    coords = Point(48.86385199985207, 2.337071483848432)  # Paris
    department_code = "75"
