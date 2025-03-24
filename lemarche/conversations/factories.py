import factory
from factory.django import DjangoModelFactory

from lemarche.conversations.models import Conversation, EmailGroup, TemplateTransactional
from lemarche.siaes.factories import SiaeFactory


class ConversationFactory(DjangoModelFactory):
    class Meta:
        model = Conversation

    title = factory.Faker("name", locale="fr_FR")
    sender_first_name = factory.Faker("name", locale="fr_FR")
    sender_last_name = factory.Faker("name", locale="fr_FR")
    sender_email = factory.Sequence("email{0}@inclusion.gouv.fr".format)
    siae = factory.SubFactory(SiaeFactory)
    initial_body_message = factory.Faker("name", locale="fr_FR")


class EmailGroupFactory(DjangoModelFactory):
    class Meta:
        model = EmailGroup

    display_name = factory.Faker("name", locale="fr_FR")
    description = factory.Faker("name", locale="fr_FR")


class TemplateTransactionalFactory(DjangoModelFactory):
    class Meta:
        model = TemplateTransactional
        django_get_or_create = ("code",)

    name = factory.Faker("name", locale="fr_FR")
    code = factory.Faker("name", locale="fr_FR")
    group = factory.SubFactory(EmailGroupFactory)
