import json
import os

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from lemarche.conversations.factories import ConversationFactory
from lemarche.conversations.models import Conversation


class InboundEmailParsingApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.conversation: Conversation = ConversationFactory()
        email_data_file_url = os.path.join(os.path.dirname(__file__), "data_inbound_tests.json")

        with open(email_data_file_url, "r") as file:
            email_data = json.load(file)
            cls.email_data = email_data.copy()
        cls.item_email_data = cls.email_data["items"][0]
        cls.item_email_data["To"][0]["Address"] = cls.conversation.email_sender_buyer_encoded
        cls.url = reverse("api:inbound-email-parsing")

    def test_inbound_serializer_parse_emails(self):
        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_inbound_emails_refresh_data_json(self):
        # assert that we have initial message in data
        self.assertEqual(len(self.conversation.data), 1)

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")

        # refresh conversation data field and check if update
        self.conversation.refresh_from_db()
        self.assertEqual(len(self.conversation.data), 2)
        self.assertEqual(response.status_code, 201)

    def test_inbound_emails_send_to_buyer(self):
        mail_subject = "test send from siae to buyer"
        self.item_email_data["To"][0]["Address"] = self.conversation.email_sender_buyer_encoded
        self.item_email_data["From"]["Address"] = self.conversation.email_sender_siae
        self.item_email_data["Subject"] = mail_subject

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # assert that we send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"[DEV] {mail_subject}")
        self.assertEqual(mail.outbox[0].from_email, self.conversation.email_sender_siae_encoded)
        self.assertEqual(mail.outbox[0].to, [self.conversation.email_sender_buyer])

    def test_inbound_emails_send_to_siae(self):
        mail_subject = "test send from buyer to siae"
        self.item_email_data["To"][0]["Address"] = self.conversation.email_sender_siae_encoded
        self.item_email_data["From"]["Address"] = self.conversation.email_sender_buyer
        self.item_email_data["Subject"] = mail_subject

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # assert that we send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"[DEV] {mail_subject}")
        self.assertEqual(mail.outbox[0].from_email, self.conversation.email_sender_buyer_encoded)
        self.assertEqual(mail.outbox[0].to, [self.conversation.email_sender_siae])
