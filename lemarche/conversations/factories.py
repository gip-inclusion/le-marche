import factory
from factory.django import DjangoModelFactory

from lemarche.conversations.models import Conversation
from lemarche.siaes.factories import SiaeFactory


class ConversationFactory(DjangoModelFactory):
    class Meta:
        model = Conversation

    title = factory.Faker("name", locale="fr_FR")
    email_sender = factory.Sequence("email{0}@beta.gouv.fr".format)
    siae = factory.SubFactory(SiaeFactory)
    initial_body_message = factory.Faker("name", locale="fr_FR")
