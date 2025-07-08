from unittest.mock import patch

from django.test import TestCase

from lemarche.conversations.factories import TemplateTransactionalFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.enums import TenderSourcesChoices
from lemarche.tenders.factories import TenderFactory, TenderSiaeFactory
from lemarche.users.factories import UserFactory
from lemarche.www.tenders.tasks import send_tender_email_to_siae


class TenderEmailTasksTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create necessary transactional templates
        email_group = TemplateTransactionalFactory().group
        cls.email_template = TemplateTransactionalFactory(
            code="TENDERS_SIAE_PRESENTATION", brevo_id=123, tally_brevo_id=456, is_active=True, group=email_group
        )

        # Create a SIAE and a user for testing
        cls.siae = SiaeFactory(contact_first_name="Jean", contact_last_name="SIAE", contact_email="siae@example.com")
        cls.user = UserFactory(
            first_name="Paul", last_name="Acheteur", email="user@example.com", company_name="Entreprise Achat"
        )

        # Create a standard tender
        cls.tender = TenderFactory(author=cls.user)
        cls.tender_siae = TenderSiaeFactory(tender=cls.tender, siae=cls.siae)

        # Create a tender from Tally source
        cls.tender_tally = TenderFactory(author=cls.user, source=TenderSourcesChoices.SOURCE_TALLY)
        cls.tender_tally_siae = TenderSiaeFactory(tender=cls.tender_tally, siae=cls.siae)

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch("lemarche.www.tenders.tasks.whitelist_recipient_list", return_value=["siae@example.com"])
    def test_send_tender_email_to_siae_standard(self, mock_whitelist, mock_send_email):
        """Test sending a standard email for a tender"""
        # Call the function with an email_subject
        send_tender_email_to_siae(self.tender_siae, "Test subject")

        # Verify that the send_transactional_email method was called
        mock_send_email.assert_called_once()

        # Verify the arguments passed to send_transactional_email
        _, kwargs = mock_send_email.call_args
        self.assertEqual(kwargs["recipient_email"], "siae@example.com")
        self.assertFalse(kwargs.get("is_from_tally", False))

        # Verify that the send date was recorded in the TenderSiae
        self.tender_siae.refresh_from_db()
        self.assertIsNotNone(self.tender_siae.email_send_date)

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch("lemarche.www.tenders.tasks.whitelist_recipient_list", return_value=["siae@example.com"])
    def test_send_tender_email_to_siae_tally(self, mock_whitelist, mock_send_email):
        """Test sending an email for a tender from Tally source"""
        # Call the function with an email_subject
        send_tender_email_to_siae(self.tender_tally_siae, "Test subject")

        # Verify that the send_transactional_email method was called
        mock_send_email.assert_called_once()

        # Verify the arguments passed to send_transactional_email
        _, kwargs = mock_send_email.call_args

        # Since the source is TALLY, we expect is_from_tally to be True
        self.assertEqual(kwargs["recipient_email"], "siae@example.com")
        self.assertTrue(kwargs.get("is_from_tally", False))

        # Verify that the send date was recorded in the TenderSiae
        self.tender_tally_siae.refresh_from_db()
        self.assertIsNotNone(self.tender_tally_siae.email_send_date)

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch("lemarche.www.tenders.tasks.whitelist_recipient_list", return_value=["override@example.com"])
    def test_send_tender_email_to_siae_with_user_override(self, mock_whitelist, mock_send_email):
        """Test sending an email to a specific user instead of the SIAE"""
        # Create a user to override the default recipient
        override_user = UserFactory(email="override@example.com")

        # Call the function with an email_subject and a recipient override
        send_tender_email_to_siae(self.tender_siae, "Test subject", recipient_to_override=override_user)

        # Verify that the send_transactional_email method was called
        mock_send_email.assert_called_once()

        # Verify the arguments passed to send_transactional_email
        _, kwargs = mock_send_email.call_args
        self.assertEqual(kwargs["recipient_email"], "override@example.com")
        self.assertFalse(kwargs.get("is_from_tally", False))

        # Verify that recipient_content_object is the override user
        self.assertEqual(kwargs["recipient_content_object"], override_user)
