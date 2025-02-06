import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.cpv.models import Code


class CodeFactory(DjangoModelFactory):
    class Meta:
        model = Code
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Faker("name", locale="fr_FR")
    # slug: auto-generated
    cpv_code = factory.fuzzy.FuzzyText(length=8, chars=string.digits)

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.sectors.add(*extracted)
