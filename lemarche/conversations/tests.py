from django.test import TestCase

from lemarche.conversations.factories import ConversationFactory
from lemarche.conversations.models import Conversation


class ConversationModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.conversation = ConversationFactory(title="Je souhaite me renseigner")

    def test_count(self):
        self.assertEqual(Conversation.objects.count(), 1)

    def test_uuid_field(self):
        self.assertEqual(len(self.conversation.uuid), 22)

    def test_str(self):
        self.assertEqual(str(self.conversation), "Je souhaite me renseigner")


class ConversationQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.conversation = ConversationFactory()
        cls.conversation_with_answer = ConversationFactory(
            data=[{"items": [{"To": [{"Name": "buyer"}], "From": {"Name": "siae"}}]}]
        )

    def test_has_answer(self):
        self.assertEqual(Conversation.objects.has_answer().count(), 1)

    def test_with_answer_count(self):
        conversation_queryset = Conversation.objects.with_answer_count()
        self.assertEqual(conversation_queryset.get(id=self.conversation.id).answer_count, 0)
        self.assertEqual(conversation_queryset.get(id=self.conversation_with_answer.id).answer_count, 1)
