import json
import os

from django.test import TestCase
from django.urls import reverse

from lemarche.conversations.factories import ConversationFactory


class InboundEmailParsingApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.conversation = ConversationFactory()

    def test_inbound_serializer_parse_emails(self):
        url = reverse("api:inbound-email-parsing")
        email_data_file_url = os.path.join(os.path.dirname(__file__), "data_inbound_tests.json")
        with open(email_data_file_url, "r") as file:
            email_data = json.load(file)
        response = self.client.post(url, data=email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
