import json
import os

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
        cls.email_data["items"][0]["To"][0]["Address"] = cls.conversation.email_sender_encoded

    def test_inbound_serializer_parse_emails(self):
        url = reverse("api:inbound-email-parsing")

        response = self.client.post(url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_inbound_serializer_receive_emails(self):
        url = reverse("api:inbound-email-parsing")
        self.assertEqual(len(self.conversation.data), 1)
        response = self.client.post(url, data=self.email_data, content_type="application/json")
        self.conversation.refresh_from_db()
        self.assertEqual(len(self.conversation.data), 2)
        self.assertEqual(response.status_code, 201)
