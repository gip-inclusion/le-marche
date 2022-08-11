import factory
from factory.django import DjangoModelFactory

from lemarche.sectors.models import Sector, SectorGroup


class SectorGroupFactory(DjangoModelFactory):
    class Meta:
        model = SectorGroup

    name = factory.Faker("name", locale="fr_FR")
    # slug auto-generated


class SectorFactory(DjangoModelFactory):
    class Meta:
        model = Sector

    name = factory.Faker("name", locale="fr_FR")
    # slug auto-generated
    group = factory.SubFactory(SectorGroupFactory)
