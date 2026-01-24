import factory
from factory.django import DjangoModelFactory

from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import (
    Siae,
    SiaeActivity,
    SiaeClientReference,
    SiaeGroup,
    SiaeImage,
    SiaeLabelOld,
    SiaeOffer,
    SiaeUserRequest,
)
from tests.sectors.factories import SectorFactory
from tests.users.factories import UserFactory


class SiaeGroupFactory(DjangoModelFactory):
    class Meta:
        model = SiaeGroup
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Sequence("Some SiaeGroup{0}".format)
    # slug auto-generated

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            self.siaes.add(*extracted)

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            self.sectors.add(*extracted)


class SiaeFactory(DjangoModelFactory):
    class Meta:
        model = Siae
        skip_postgeneration_save = True

    name = factory.Sequence("Some Siae N°{0}".format)
    # slug auto-generated
    kind = siae_constants.KIND_EI
    nature = [siae_constants.NATURE_HEAD_OFFICE]
    # Don't start a SIRET with 0.
    siret = "1234567891234"
    address = "1 rue de la paix"
    city = "Rennes"
    post_code = "35000"
    department = "35"
    region = "Bretagne"
    contact_email = factory.Sequence("siae_contact_email{0}@inclusion.gouv.fr".format)
    contact_first_name = "Jean"
    contact_last_name = "Lejean"

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if extracted:
            self.users.add(*extracted)

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
            geo_range_custom_distance=30,
        )
        with_zones_perimeter = factory.Trait(geo_range=siae_constants.GEO_RANGE_ZONES)

    sector = factory.SubFactory(SectorFactory)
    presta_type = [siae_constants.PRESTA_DISP]

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if extracted:
            self.locations.add(*extracted)


class SiaeOfferFactory(DjangoModelFactory):
    class Meta:
        model = SiaeOffer

    name = "Some SiaeOffer"


class SiaeClientReferenceFactory(DjangoModelFactory):
    class Meta:
        model = SiaeClientReference

    name = factory.Sequence("Some SiaeClientReference N°:{0}".format)


class SiaeLabelOldFactory(DjangoModelFactory):
    class Meta:
        model = SiaeLabelOld

    name = "Some SiaeLabelOld"


class SiaeImageFactory(DjangoModelFactory):
    class Meta:
        model = SiaeImage


class SiaeUserRequestFactory(DjangoModelFactory):
    class Meta:
        model = SiaeUserRequest
        skip_postgeneration_save = True

    siae = factory.SubFactory(SiaeFactory)
    initiator = factory.SubFactory(UserFactory)
    assignee = factory.SubFactory(UserFactory)
    logs = factory.LazyFunction(list)

    @factory.post_generation
    def ensure_assignee_membership(self, create, extracted, **kwargs):
        if create and self.assignee and self.siae:
            self.siae.users.add(self.assignee)
