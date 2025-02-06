import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.sectors.factories import SectorGroupFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import (
    Siae,
    SiaeActivity,
    SiaeClientReference,
    SiaeGroup,
    SiaeImage,
    SiaeLabelOld,
    SiaeOffer,
)


class SiaeGroupFactory(DjangoModelFactory):
    class Meta:
        model = SiaeGroup
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Faker("company", locale="fr_FR")
    # slug auto-generated

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            self.siaes.add(*extracted)


class SiaeFactory(DjangoModelFactory):
    class Meta:
        model = Siae
        skip_postgeneration_save = True

    name = factory.Faker("company", locale="fr_FR")
    # slug auto-generated
    kind = siae_constants.KIND_EI
    nature = factory.fuzzy.FuzzyChoice([key for (key, value) in siae_constants.NATURE_CHOICES])
    presta_type = factory.List([factory.fuzzy.FuzzyChoice([key for (key, value) in siae_constants.PRESTA_CHOICES])])
    # Don't start a SIRET with 0.
    siret = factory.fuzzy.FuzzyText(length=13, chars=string.digits, prefix="1")
    address = factory.Faker("street_address", locale="fr_FR")
    city = factory.Faker("city", locale="fr_FR")
    post_code = factory.Faker("postalcode")
    department = "35"
    region = "Bretagne"
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


class SiaeActivityFactory(DjangoModelFactory):
    class Meta:
        model = SiaeActivity
        skip_postgeneration_save = True  # Prevents unnecessary save

    class Params:
        with_country_perimeter = factory.Trait(geo_range=siae_constants.GEO_RANGE_COUNTRY)
        with_custom_distance_perimeter = factory.Trait(
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=factory.fuzzy.FuzzyInteger(1, 100),
        )
        with_zones_perimeter = factory.Trait(geo_range=siae_constants.GEO_RANGE_ZONES)

    sector_group = factory.SubFactory(SectorGroupFactory)

    presta_type = factory.List([factory.fuzzy.FuzzyChoice([key for (key, _) in siae_constants.PRESTA_CHOICES])])

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            self.sectors.add(*extracted)

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if extracted:
            self.locations.add(*extracted)


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


class SiaeImageFactory(DjangoModelFactory):
    class Meta:
        model = SiaeImage

    name = factory.Faker("name", locale="fr_FR")
