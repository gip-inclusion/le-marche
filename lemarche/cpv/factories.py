import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.cpv.models import Code


class CodeFactory(DjangoModelFactory):
    class Meta:
        model = Code

    name = factory.Faker("name", locale="fr_FR")
    # slug is auto-generated
    # cpv_code = factory.Faker("barcode", length=8)
    cpv_code = factory.fuzzy.FuzzyText(length=8, chars=string.digits)
