from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from lemarche.conversations import constants as conversation_constants
from lemarche.conversations.factories import ConversationFactory, TemplateTransactionalFactory
from lemarche.conversations.models import Conversation, TemplateTransactional
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

    def test_with_answer_stats(self):
        conversation_queryset = Conversation.objects.with_answer_stats()
        self.assertEqual(conversation_queryset.get(id=self.conversation.id).answer_count_annotated, 0)
        self.assertEqual(conversation_queryset.get(id=self.conversation_with_answer.id).answer_count_annotated, 1)

    def test_outdated(self):
        one_year_ago = timezone.now() - timedelta(days=365)
        ConversationFactory(created_at=one_year_ago)
        five_weeks_ago = timezone.now() - timedelta(weeks=5)
        ConversationFactory(created_at=five_weeks_ago)
        self.assertEqual(Conversation.objects.all().count(), 2 + 2)
        self.assertEqual(Conversation.objects.outdated().count(), 1)


class TemplateTransactionalModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tt_inactive = TemplateTransactional(
            code="EMAIL_1", mailjet_id=10, brevo_id=11, source=conversation_constants.SOURCE_MAILJET, is_active=False
        )
        cls.tt_active_empty = TemplateTransactional(
            code="EMAIL_2", source=conversation_constants.SOURCE_MAILJET, is_active=False
        )
        cls.tt_active_mailjet = TemplateTransactional(
            code="EMAIL_3", mailjet_id=30, brevo_id=31, source=conversation_constants.SOURCE_MAILJET, is_active=True
        )
        cls.tt_active_brevo = TemplateTransactional(
            code="EMAIL_4", mailjet_id=40, brevo_id=41, source=conversation_constants.SOURCE_BREVO, is_active=True
        )

    def test_get_template_id(self):
        self.assertIsNone(self.tt_active_empty.get_template_id)
        self.assertEqual(self.tt_inactive.get_template_id, self.tt_inactive.mailjet_id)
        self.assertEqual(self.tt_active_mailjet.get_template_id, self.tt_active_mailjet.mailjet_id)
        self.assertEqual(self.tt_active_brevo.get_template_id, self.tt_active_brevo.brevo_id)


class TemplateTransactionalModelSaveTest(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_template_transactional_validation_on_save(self):
        TemplateTransactionalFactory(
            mailjet_id=None, brevo_id=None, source=conversation_constants.SOURCE_BREVO, is_active=False
        )
        self.assertRaises(IntegrityError, TemplateTransactionalFactory, source=None)
        self.assertRaises(
            ValidationError,
            TemplateTransactionalFactory,
            mailjet_id=123,
            brevo_id=None,
            source=conversation_constants.SOURCE_BREVO,
            is_active=True,
        )
        self.assertRaises(
            ValidationError,
            TemplateTransactionalFactory,
            mailjet_id=None,
            brevo_id=123,
            source=conversation_constants.SOURCE_MAILJET,
            is_active=True,
        )
