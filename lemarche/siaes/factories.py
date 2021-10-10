import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.siaes.models import Siae, SiaeOffer


class SiaeFactory(DjangoModelFactory):
    class Meta:
        model = Siae

    name = factory.Faker("company", locale="fr_FR")
    kind = Siae.KIND_EI
    nature = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.NATURE_CHOICES])
    presta_type = factory.List([factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.PRESTA_CHOICES])])
    # Don't start a SIRET with 0.
    siret = factory.fuzzy.FuzzyText(length=13, chars=string.digits, prefix="1")
    address = factory.Faker("street_address", locale="fr_FR")
    city = factory.Faker("city", locale="fr_FR")
    post_code = factory.Faker("postalcode")
    department = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.DEPARTMENT_CHOICES])


class SiaeOfferFactory(DjangoModelFactory):
    class Meta:
        model = SiaeOffer

    name = factory.Faker("name")
