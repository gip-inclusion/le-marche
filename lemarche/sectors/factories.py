import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from lemarche.sectors.models import Sector, SectorGroup


class SectorGroupFactory(DjangoModelFactory):
    class Meta:
        model = SectorGroup

    name = factory.Faker("name")
    # TODO: model method to create slug on save() instead
    slug = factory.LazyAttribute(lambda o: slugify(o.name))


class SectorFactory(DjangoModelFactory):
    class Meta:
        model = Sector

    name = factory.Faker("name")
    # TODO: model method to create slug on save() instead
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    group = factory.SubFactory(SectorGroupFactory)
