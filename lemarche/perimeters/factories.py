import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from lemarche.perimeters.models import Perimeter


class PerimeterFactory(DjangoModelFactory):
    class Meta:
        model = Perimeter

    name = factory.Faker("name")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    kind = Perimeter.KIND_CITY
