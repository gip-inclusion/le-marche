from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter


def test_factory():
    PerimeterFactory()
    assert Perimeter.objects.count() == 1
