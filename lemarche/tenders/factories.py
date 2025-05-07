from datetime import date, timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import PartnerShareTender, QuestionAnswer, Tender, TenderQuestion, TenderSiae
from lemarche.users.factories import UserFactory


class TenderFactory(DjangoModelFactory):
    class Meta:
        model = Tender
        skip_postgeneration_save = True  # Prevents unnecessary save

    title = factory.Faker("name", locale="fr_FR")
    # slug auto-generated
    kind = tender_constants.KIND_QUOTE
    presta_type = []
    response_kind = [
        tender_constants.RESPONSE_KIND_EMAIL,
        tender_constants.RESPONSE_KIND_TEL,
        tender_constants.RESPONSE_KIND_EXTERNAL,
    ]
    description = "Ceci est un pagagraphe de test"
    constraints = "Ceci est un pagagraphe de test"
    deadline_date = date.today() + timedelta(days=10)
    start_working_date = date.today() + timedelta(days=50)
    author = factory.SubFactory(UserFactory)
    external_link = "https://www.example.com"
    # Contact fields
    contact_first_name = factory.Sequence("first_name{0}".format)
    contact_last_name = factory.Sequence("last_name{0}".format)
    contact_email = factory.Sequence("email_contact_tender{0}@example.com".format)
    contact_phone = "0123456789"
    status = tender_constants.STATUS_SENT
    validated_at = timezone.now()
    first_sent_at = timezone.now()

    @factory.post_generation
    def perimeters(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.perimeters.add(*extracted)

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.sectors.add(*extracted)

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.siaes.add(*extracted)

    @factory.post_generation
    def admins(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.admins.add(*extracted)


class TenderQuestionFactory(DjangoModelFactory):
    class Meta:
        model = TenderQuestion

    text = "How do you do ?"


class QuestionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = QuestionAnswer

    question = factory.SubFactory(TenderQuestionFactory)
    siae = factory.SubFactory(SiaeFactory)
    answer = "Yes I do"


class PartnerShareTenderFactory(DjangoModelFactory):
    class Meta:
        model = PartnerShareTender
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Faker("name", locale="fr_FR")

    contact_email_list = factory.LazyFunction(lambda: [factory.Faker("email", locale="fr_FR") for i in range(4)])

    @factory.post_generation
    def perimeters(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.perimeters.add(*extracted)


class TenderSiaeFactory(DjangoModelFactory):
    class Meta:
        model = TenderSiae

    tender = factory.SubFactory(TenderFactory)
    siae = factory.SubFactory(SiaeFactory)
