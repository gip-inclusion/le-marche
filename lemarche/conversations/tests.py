from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings

from lemarche.conversations.constants import ATTRIBUTES_TO_NOT_ANONYMIZE_FOR_INBOUND, ATTRIBUTES_TO_SAVE_FOR_INBOUND
from lemarche.conversations.factories import ConversationFactory, EmailGroupFactory, TemplateTransactionalFactory
from lemarche.conversations.models import Conversation, DisabledEmail, TemplateTransactional
from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory


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


@patch("django.utils.timezone.now", lambda: datetime(year=2024, month=1, day=1, tzinfo=datetime_timezone.utc))
@override_settings(
    INACTIVE_CONVERSATION_TIMEOUT_IN_MONTHS=6,
)
class ConversationAnonymizationTestCase(TestCase):
    """
    Check that conversation are correctly anonymized
    """

    def setUp(self):
        inbound_data = {key: "something" for key in ATTRIBUTES_TO_SAVE_FOR_INBOUND}
        self.anonymized_inbound_data = {key: "something" for key in ATTRIBUTES_TO_NOT_ANONYMIZE_FOR_INBOUND}

        ConversationFactory(
            title="anonymized",
            created_at=datetime(year=2023, month=6, day=1, tzinfo=datetime_timezone.utc),
            initial_body_message="blabla",
            data=[inbound_data, inbound_data],
        )
        ConversationFactory(created_at=datetime(year=2023, month=8, day=1, tzinfo=datetime_timezone.utc))

    def test_anonymize_command(self):
        call_command("anonymize_outdated_conversations")

        conv_anonymized = Conversation.objects.get(title="anonymized", is_anonymized=True)
        self.assertIsNone(conv_anonymized.sender_user)
        self.assertIsNone(conv_anonymized.sender_email)
        self.assertEqual(conv_anonymized.sender_first_name, "")
        self.assertEqual(conv_anonymized.sender_last_name, "")
        self.assertEqual(conv_anonymized.initial_body_message, "6")
        self.assertEqual(conv_anonymized.data, [self.anonymized_inbound_data, self.anonymized_inbound_data])

        self.assertTrue(Conversation.objects.get(is_anonymized=False), msg="active conversation wrongly anonymised !!")


class TemplateTransactionalModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.email_group = EmailGroupFactory()
        cls.tt_inactive = TemplateTransactional(
            name="Email 1", code="EMAIL_1", brevo_id=11, is_active=False, group=cls.email_group
        )
        cls.tt_active_empty = TemplateTransactional(
            name="Email 2", code="EMAIL_2", is_active=False, group=cls.email_group
        )
        cls.tt_active_brevo = TemplateTransactional(
            name="Email 3", code="EMAIL_3", brevo_id=41, is_active=True, group=cls.email_group
        )
        cls.tt_active_tally = TemplateTransactional(
            name="Email 4", code="EMAIL_4", brevo_id=42, tally_brevo_id=43, is_active=True, group=cls.email_group
        )

    def test_get_template_id(self):
        self.assertIsNone(self.tt_active_empty.get_template_id())
        self.assertEqual(self.tt_inactive.get_template_id(), self.tt_inactive.brevo_id)
        self.assertEqual(self.tt_active_brevo.get_template_id(), self.tt_active_brevo.brevo_id)
        # Test that when is_from_tally is False, it returns the default brevo_id
        self.assertEqual(self.tt_active_tally.get_template_id(), self.tt_active_tally.brevo_id)
        # Test that when is_from_tally is True, it returns the tally_brevo_id
        self.assertEqual(self.tt_active_tally.get_template_id(is_from_tally=True), self.tt_active_tally.tally_brevo_id)

    @patch("lemarche.conversations.models.api_brevo.BrevoTransactionalEmailApiClient")
    def test_send_transactional_email_brevo(self, mock_brevo_client_class):
        mock_instance = mock_brevo_client_class.return_value
        self.tt_active_brevo.save()
        self.tt_active_brevo.send_transactional_email(
            recipient_email="test@example.com", recipient_name="test", variables={}
        )
        mock_instance.send_transactional_email_with_template.assert_called_once()
        # Check is_from_tally parameter is passed correctly
        args, kwargs = mock_instance.send_transactional_email_with_template.call_args
        self.assertFalse(kwargs.get("is_from_tally", False))

    @patch("lemarche.conversations.models.api_brevo.BrevoTransactionalEmailApiClient")
    def test_send_transactional_email_tally(self, mock_brevo_client_class):
        mock_instance = mock_brevo_client_class.return_value
        self.tt_active_tally.save()
        self.tt_active_tally.send_transactional_email(
            recipient_email="test@example.com", recipient_name="test", variables={}, is_from_tally=True
        )
        mock_instance.send_transactional_email_with_template.assert_called_once()
        # Check is_from_tally parameter is passed correctly
        _, kwargs = mock_instance.send_transactional_email_with_template.call_args
        # Check template_id is the tally one
        self.assertEqual(kwargs.get("template_id"), self.tt_active_tally.tally_brevo_id)

    @patch("lemarche.conversations.models.api_brevo.BrevoTransactionalEmailApiClient")
    def test_send_transactional_email_inactive(self, mock_brevo_client_class):
        mock_instance = mock_brevo_client_class.return_value
        self.tt_inactive.save()
        self.tt_inactive.send_transactional_email(
            recipient_email="test@example.com", recipient_name="test", variables={}
        )
        mock_instance.send_transactional_email_with_template.assert_not_called()

    @patch("lemarche.conversations.models.api_brevo.BrevoTransactionalEmailApiClient")
    def test_disabled_email_group(self, mock_brevo_client_class):
        mock_instance = mock_brevo_client_class.return_value
        email_test = "test@example.com"
        user = UserFactory(email=email_test)
        DisabledEmail.objects.create(user=user, group=self.email_group)

        self.tt_active_brevo.save()
        self.tt_active_brevo.send_transactional_email(recipient_email=email_test, recipient_name="test", variables={})
        mock_instance.send_transactional_email_with_template.assert_not_called()


class TemplateTransactionalModelSaveTest(TransactionTestCase):
    def test_template_transactional_validation_on_save(self):
        self.assertRaises(ValidationError, TemplateTransactionalFactory, brevo_id=None, is_active=True, group=None)
