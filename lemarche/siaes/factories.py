import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.siaes.models import Siae, SiaeClientReference, SiaeGroup, SiaeLabel, SiaeOffer


class SiaeGroupFactory(DjangoModelFactory):
    class Meta:
        model = SiaeGroup

    name = factory.Faker("company", locale="fr_FR")
    # slug auto-generated


class SiaeFactory(DjangoModelFactory):
    class Meta:
        model = Siae

    name = factory.Faker("company", locale="fr_FR")
    # slug auto-generated
    kind = Siae.KIND_EI
    nature = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.NATURE_CHOICES])
    presta_type = factory.List([factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.PRESTA_CHOICES])])
    # Don't start a SIRET with 0.
    siret = factory.fuzzy.FuzzyText(length=13, chars=string.digits, prefix="1")
    address = factory.Faker("street_address", locale="fr_FR")
    city = factory.Faker("city", locale="fr_FR")
    post_code = factory.Faker("postalcode")
    department = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.DEPARTMENT_CHOICES])
    region = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.REGION_CHOICES])
    contact_email = factory.Sequence("email{0}@example.com".format)


class SiaeOfferFactory(DjangoModelFactory):
    class Meta:
        model = SiaeOffer

    name = factory.Faker("name")


class SiaeClientReferenceFactory(DjangoModelFactory):
    class Meta:
        model = SiaeClientReference

    name = factory.Faker("name")


class SiaeLabelFactory(DjangoModelFactory):
    class Meta:
        model = SiaeLabel

    name = factory.Faker("name")
