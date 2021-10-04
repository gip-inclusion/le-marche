import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from lemarche.sectors.models import Sector


class SectorFactory(DjangoModelFactory):
    class Meta:
        model = Sector

    name = factory.Faker("name")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    # group =
