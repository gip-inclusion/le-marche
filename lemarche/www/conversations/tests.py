from unittest import mock

from django.test import TestCase

from lemarche.companies.factories import CompanyFactory
from lemarche.conversations.factories import ConversationFactory
from lemarche.users.factories import UserFactory
from lemarche.utils import constants
from lemarche.www.conversations.tasks import send_first_email_from_conversation


class TestConversationTasks(TestCase):
    def test_send_first_email_from_conversation(self):
        conversation = ConversationFactory()

        with mock.patch("lemarche.www.conversations.tasks.send_mail_async") as mock_send_mail_async:
            send_first_email_from_conversation(conversation)

        mock_send_mail_async.assert_called_once()
        email_body = mock_send_mail_async.call_args[1]["email_body"]
        self.assertTrue(f"{conversation.sender_first_name} {conversation.sender_last_name}" in email_body)
        self.assertTrue("Ce client vous a contacté via le Marché de l'inclusion." in email_body)

        # conversation with authenticated user

        company = CompanyFactory.build()
        user_buyer = UserFactory(
            kind=constants.USER_KIND_BUYER,
            company_name=company.name,
        )

        conversation_with_user = ConversationFactory(sender_user=user_buyer)
        with mock.patch("lemarche.www.conversations.tasks.send_mail_async") as mock_send_mail_async:
            send_first_email_from_conversation(conversation_with_user)

        mock_send_mail_async.assert_called_once()
        email_body = mock_send_mail_async.call_args[1]["email_body"]
        self.assertTrue(
            f"{conversation_with_user.sender_first_name} {conversation_with_user.sender_last_name}" in email_body
        )
        self.assertTrue(company.name in email_body)
        self.assertTrue("Ce client vous a contacté via le Marché de l'inclusion." in email_body)
