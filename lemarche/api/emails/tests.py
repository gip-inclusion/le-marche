import json
import os

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from lemarche.conversations.factories import ConversationFactory
from lemarche.conversations.models import Conversation


class InboundEmailParsingApiTestV0(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.conv: Conversation = ConversationFactory(version=0)
        email_data_file_url = os.path.join(os.path.dirname(__file__), "data_inbound_tests.json")

        with open(email_data_file_url, "r") as file:
            email_data = json.load(file)
            cls.email_data = email_data.copy()
        cls.item_email_data = cls.email_data["items"][0]
        cls.item_email_data["To"][0]["Address"] = cls.conv.sender_email_buyer_encoded
        cls.url = reverse("api:inbound-email-parsing")

    def test_encoded_items(self):
        # test sender and siae encoded format
        # self.conv.uuid = "MjpaVwLGJBUwdKpkYJHqNr"
        # sender_email_buyer_encoded= 'MjpaVwLGJBUwdKpkYJHqNr_b@reply.staging.lemarche.inclusion.beta.gouv.fr'
        sender_encoded = self.conv.sender_email_buyer_encoded.split("@")[0]
        self.assertEqual(sender_encoded.split("_")[0], self.conv.uuid)
        sender_conv = Conversation.objects.get_conv_from_uuid(conv_uuid=sender_encoded.split("_")[0], version=0)
        self.assertEqual(sender_conv, self.conv)
        # sender_email_siae_encoded= 'MjpaVwLGJBUwdKpkYJHqNr_b@reply.staging.lemarche.inclusion.beta.gouv.fr'
        siae_encoded = self.conv.sender_email_siae_encoded.split("@")[0]
        self.assertEqual(siae_encoded.split("_")[0], self.conv.uuid)
        siae_conv = Conversation.objects.get_conv_from_uuid(conv_uuid=siae_encoded.split("_")[0], version=0)
        self.assertEqual(siae_conv, self.conv)

    def test_inbound_serializer_parse_emails(self):
        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_inbound_emails_refresh_data_json(self):
        # assert that we have initial message in data
        self.assertEqual(len(self.conv.data), 0)

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")

        # refresh conversation data field and check if update
        self.conv.refresh_from_db()
        self.assertEqual(len(self.conv.data), 1)
        self.assertEqual(response.status_code, 201)

    def test_inbound_emails_send_to_buyer(self):
        mail_subject = "test send from siae to buyer"
        self.item_email_data["To"][0]["Address"] = self.conv.sender_email_buyer_encoded
        self.item_email_data["From"]["Address"] = self.conv.sender_email_siae
        self.item_email_data["Subject"] = mail_subject

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # assert that we send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"[DEV] {mail_subject}")
        self.assertEqual(
            mail.outbox[0].from_email,
            f"{self.conv.siae.contact_full_name} <{self.conv.sender_email_siae_encoded}>",
        )
        self.assertEqual(mail.outbox[0].to, [self.conv.sender_email_buyer])

    def test_inbound_emails_send_to_siae(self):
        mail_subject = "test send from buyer to siae"
        self.item_email_data["To"][0]["Address"] = self.conv.sender_email_siae_encoded
        self.item_email_data["From"]["Address"] = self.conv.sender_email_buyer
        self.item_email_data["Subject"] = mail_subject

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # assert that we send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"[DEV] {mail_subject}")

        self.assertEqual(
            mail.outbox[0].from_email,
            f"{self.conv.sender_first_name} {self.conv.sender_last_name} <{self.conv.sender_email_buyer_encoded}>",
        )
        self.assertEqual(mail.outbox[0].to, [self.conv.sender_email_siae])


class InboundEmailParsingApiTest(TestCase):
    # Conversation V1 test
    @classmethod
    def setUpTestData(cls):
        cls.conv: Conversation = ConversationFactory(version=1)
        email_data_file_url = os.path.join(os.path.dirname(__file__), "data_inbound_tests.json")

        with open(email_data_file_url, "r") as file:
            email_data = json.load(file)
            cls.email_data = email_data.copy()
        cls.item_email_data = cls.email_data["items"][0]
        cls.item_email_data["To"][0]["Address"] = cls.conv.sender_email_buyer_encoded
        cls.url = reverse("api:inbound-email-parsing")

    def test_inbound_serializer_parse_emails(self):
        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_encoded_items(self):
        # test sender and siae encoded format
        # self.conv.sender_encoded = 'alexandre_delahaye_du_wagner_yves_thomas_3b81'
        # self.conv.sender_full_name = "Alexandre Delahaye du Wagner Yves Thomas"
        self.assertEqual(self.conv.sender_encoded.split("_")[:-1], slugify(self.conv.sender_full_name).split("-"))
        sender_conv = Conversation.objects.get_conv_from_uuid(conv_uuid=self.conv.sender_encoded, version=1)
        self.assertEqual(sender_conv, self.conv)
        # self.conv.siae_encoded = 'aime_bailly_josephine_vincent_perez_d243'
        # self.conv.siae.contact_full_name = "Alexandre Delahaye du Wagner Yves Thomas"
        self.assertEqual(self.conv.siae_encoded.split("_")[:-1], slugify(self.conv.siae.contact_full_name).split("-"))
        siae_conv = Conversation.objects.get_conv_from_uuid(conv_uuid=self.conv.siae_encoded, version=1)
        self.assertEqual(siae_conv, self.conv)

    def test_inbound_emails_refresh_data_json(self):
        # assert that we have initial message in data
        self.assertEqual(len(self.conv.data), 0)

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")

        # refresh conversation data field and check if update
        self.conv.refresh_from_db()
        self.assertEqual(len(self.conv.data), 1)
        self.assertEqual(response.status_code, 201)

    def test_inbound_emails_send_to_buyer(self):
        mail_subject = "test send from siae to buyer"
        self.item_email_data["To"][0]["Address"] = self.conv.sender_email_buyer_encoded
        self.item_email_data["From"]["Address"] = self.conv.sender_email_siae
        self.item_email_data["Subject"] = mail_subject

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # assert that we send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"[DEV] {mail_subject}")
        self.assertEqual(
            mail.outbox[0].from_email,
            f"{self.conv.siae.contact_full_name} <{self.conv.sender_email_siae_encoded}>",
        )
        self.assertEqual(mail.outbox[0].to, [self.conv.sender_email_buyer])

    def test_inbound_emails_send_to_siae(self):
        mail_subject = "test send from buyer to siae"
        self.item_email_data["To"][0]["Address"] = self.conv.sender_email_siae_encoded
        self.item_email_data["From"]["Address"] = self.conv.sender_email_buyer
        self.item_email_data["Subject"] = mail_subject

        response = self.client.post(self.url, data=self.email_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # assert that we send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"[DEV] {mail_subject}")

        self.assertEqual(
            mail.outbox[0].from_email,
            f"{self.conv.sender_first_name} {self.conv.sender_last_name} <{self.conv.sender_email_buyer_encoded}>",
        )
        self.assertEqual(mail.outbox[0].to, [self.conv.sender_email_siae])
