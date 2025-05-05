import factory
from factory.django import DjangoModelFactory

from lemarche.cpv.models import Code


class CodeFactory(DjangoModelFactory):
    class Meta:
        model = Code
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Sequence("Some Code name N°:{0}".format)
    # slug: auto-generated
    cpv_code = "12345678"

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.sectors.add(*extracted)
