import factory
from factory.django import DjangoModelFactory

from lemarche.conversations.models import Conversation, EmailGroup, TemplateTransactional
from tests.siaes.factories import SiaeFactory


class ConversationFactory(DjangoModelFactory):
    class Meta:
        model = Conversation

    title = "Some Conversation Title"
    sender_first_name = "Jean"
    sender_last_name = "Lejean"
    sender_email = factory.Sequence("email{0}@inclusion.gouv.fr".format)
    siae = factory.SubFactory(SiaeFactory)
    initial_body_message = "Bien ou bien ?"


class EmailGroupFactory(DjangoModelFactory):
    class Meta:
        model = EmailGroup


class TemplateTransactionalFactory(DjangoModelFactory):
    class Meta:
        model = TemplateTransactional
        django_get_or_create = ("code",)

    name = "Some TemplateTransactional"
    code = "FAKE_CODE"
    group = factory.SubFactory(EmailGroupFactory)
