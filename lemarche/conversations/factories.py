import factory
from factory.django import DjangoModelFactory

from lemarche.conversations.models import Conversation
from lemarche.siaes.factories import SiaeFactory


class ConversationFactory(DjangoModelFactory):
    class Meta:
        model = Conversation

    title = factory.Faker("name", locale="fr_FR")
    email_sender = factory.Sequence("email{0}@example.com".format)
    siae = factory.SubFactory(SiaeFactory)

    @factory.post_generation
    def data(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.data.append({"email": obj.email_sender, "subject": obj.title, "body_message": obj.title})
        obj.save()
