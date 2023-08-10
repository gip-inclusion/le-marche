import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeGroup, SiaeLabelOld, SiaeOffer


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
    kind = siae_constants.KIND_EI
    nature = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.NATURE_CHOICES])
    presta_type = factory.List([factory.fuzzy.FuzzyChoice([key for (key, value) in siae_constants.PRESTA_CHOICES])])
    # Don't start a SIRET with 0.
    siret = factory.fuzzy.FuzzyText(length=13, chars=string.digits, prefix="1")
    address = factory.Faker("street_address", locale="fr_FR")
    city = factory.Faker("city", locale="fr_FR")
    post_code = factory.Faker("postalcode")
    department = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.DEPARTMENT_CHOICES])
    region = factory.fuzzy.FuzzyChoice([key for (key, value) in Siae.REGION_CHOICES])
    contact_email = factory.Sequence("siae_contact_email{0}@beta.gouv.fr".format)
    contact_first_name = factory.Faker("name", locale="fr_FR")
    contact_last_name = factory.Faker("name", locale="fr_FR")

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if extracted:
            self.users.add(*extracted)

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            self.sectors.add(*extracted)

    @factory.post_generation
    def networks(self, create, extracted, **kwargs):
        if extracted:
            self.networks.add(*extracted)


class SiaeOfferFactory(DjangoModelFactory):
    class Meta:
        model = SiaeOffer

    name = factory.Faker("name", locale="fr_FR")


class SiaeClientReferenceFactory(DjangoModelFactory):
    class Meta:
        model = SiaeClientReference

    name = factory.Faker("name", locale="fr_FR")


class SiaeLabelOldFactory(DjangoModelFactory):
    class Meta:
        model = SiaeLabelOld

    name = factory.Faker("name", locale="fr_FR")
