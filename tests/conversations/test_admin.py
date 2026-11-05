from django.contrib.admin.sites import AdminSite
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase

from lemarche.conversations.admin import ConversationAdmin
from lemarche.conversations.models import Conversation


class ConversationAdminDataDisplayTest(SimpleTestCase):
    def test_data_display_escapes_sender_metadata(self):
        model_admin = ConversationAdmin(Conversation, AdminSite())
        conversation = Conversation(
            data=[
                {
                    "From": {"Name": '<img src=x onerror="alert(1)">', "Address": "sender@example.com"},
                    "To": [{"Address": "recipient@example.com"}],
                    "SentAtDate": "2026-01-01T10:00:00Z",
                }
            ]
        )
        html = model_admin.data_display(conversation)
        self.assertIn('id="table_filter_data_message"', html)
        self.assertNotIn("<img", html)

    def test_messages_table_script_does_not_use_inner_html(self):
        # sender metadata (From.Name, From.Address) is attacker controlled: it must be inserted as text
        script_path = finders.find("js/filter_data_message.js")
        self.assertIsNotNone(script_path)
        with open(script_path, encoding="utf-8") as f:
            script = f.read()
        self.assertNotIn("innerHTML", script)
        self.assertIn("textContent", script)
