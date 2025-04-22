import factory
from factory.django import DjangoModelFactory

from lemarche.sectors.models import Sector, SectorGroup


class SectorGroupFactory(DjangoModelFactory):
    class Meta:
        model = SectorGroup

    name = factory.Sequence("Some SectorGroup N°:{0}".format)
    # slug auto-generated


class SectorFactory(DjangoModelFactory):
    class Meta:
        model = Sector
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Sequence("Some Sector N°:{0}".format)
    # slug auto-generated
    group = factory.SubFactory(SectorGroupFactory)

    @factory.post_generation
    def tenders(self, create, extracted, **kwargs):
        if extracted:
            self.tenders.add(*extracted)
