from django.test import TestCase

from lemarche.conversations.factories import ConversationFactory
from lemarche.conversations.models import Conversation
from lemarche.siaes.factories import SiaeFactory


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


class ConversationModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_with_contact_full_name = SiaeFactory(
            name="Une structure",
            contact_first_name="Prénom",
            contact_last_name="Nom",
            contact_email="siae@example.com",
        )
        cls.conversation_1 = ConversationFactory(
            title="Je souhaite me renseigner",
            sender_first_name="Acheteur",
            sender_last_name="Curieux",
            sender_email="buyer@example.com",
            siae=cls.siae_with_contact_full_name,
        )
        cls.siae_without_contact_full_name = SiaeFactory(
            name="Une autre structure", contact_first_name="", contact_last_name="", contact_email="siae@example.com"
        )
        cls.conversation_2 = ConversationFactory(
            title="Je souhaite encore me renseigner", siae=cls.siae_without_contact_full_name
        )

    def test_set_siae_encoded(self):
        self.assertTrue("acheteur_curieux" in self.conversation_1.sender_encoded)
        self.assertTrue("prenom_nom" in self.conversation_1.siae_encoded)
        self.assertTrue("une_autre_structure" in self.conversation_2.siae_encoded)


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
