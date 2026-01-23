import factory
from factory.django import DjangoModelFactory

from lemarche.jobs.models import Appellation, Rome


class RomeFactory(DjangoModelFactory):
    class Meta:
        model = Rome

    name = factory.Sequence("Some Rome N°:{0}".format)
    code = factory.Sequence("A{0}".format)


class AppellationFactory(DjangoModelFactory):
    class Meta:
        model = Appellation

    name = factory.Sequence("Some Appellation N°:{0}".format)
    code = factory.Sequence("A{0}".format)
    rome = factory.SubFactory(RomeFactory)

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            self.sectors.add(*extracted)
