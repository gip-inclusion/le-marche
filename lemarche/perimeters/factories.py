import factory
import factory.fuzzy
from django.contrib.gis.geos import Point
from factory.django import DjangoModelFactory

from lemarche.perimeters.models import Perimeter
from lemarche.siaes.models import Siae


class PerimeterFactory(DjangoModelFactory):
    class Meta:
        model = Perimeter

    name = factory.Faker("name")
    # slug is auto-generated
    kind = Perimeter.KIND_CITY
    insee_code = factory.Sequence(lambda n: n)
    # paris
    coords = Point(48.86385199985207, 2.337071483848432)
    department_code = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.DEPARTMENT_CHOICES])
