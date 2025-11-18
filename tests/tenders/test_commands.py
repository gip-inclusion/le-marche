from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import factory
from django.core.management import call_command
from django.db.models import signals
from django.test import TestCase
from django.utils import timezone

from lemarche.siaes import constants as siae_constants
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.models import User
from tests.conversations.factories import TemplateTransactionalFactory
from tests.sectors.factories import SectorFactory
from tests.siaes.factories import SiaeActivityFactory, SiaeFactory
from tests.tenders.factories import TenderFactory, TenderSiaeFactory
from tests.users.factories import UserFactory


class TestSendAuthorListOfSuperSiaesEmails(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()

        cls.siae1 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        SiaeActivityFactory(
            siae=cls.siae1,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
            sector=cls.sector,
        )
        cls.siae2 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        SiaeActivityFactory(
            siae=cls.siae2,
            sector=cls.sector,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )

        cls.siae3 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        SiaeActivityFactory(
            siae=cls.siae3,
            sector=cls.sector,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )

        cls.author = UserFactory(kind=User.KIND_BUYER)
        cls.tender_before = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD],
            sectors=[cls.sector],
            is_country_area=True,
            first_sent_at=timezone.make_aware(timezone.datetime(2024, 4, 7, 15)),
            author=cls.author,
        )
        cls.tender_before.set_siae_found_list()
        cls.tender_before.refresh_from_db()

        cls.tender_during1 = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD],
            sectors=[cls.sector],
            is_country_area=True,
            first_sent_at=timezone.make_aware(timezone.datetime(2024, 4, 8, 9)),
            author=cls.author,
        )
        cls.tender_during1.set_siae_found_list()
        cls.tender_during1.refresh_from_db()

        cls.tender_during2 = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD],
            sectors=[cls.sector],
            is_country_area=True,
            first_sent_at=timezone.make_aware(timezone.datetime(2024, 4, 8, 15)),
            author=cls.author,
        )
        cls.tender_during2.set_siae_found_list()
        cls.tender_during2.refresh_from_db()

        # Tender with siaes interested
        cls.tender_during3 = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD],
            sectors=[cls.sector],
            is_country_area=True,
            first_sent_at=timezone.make_aware(timezone.datetime(2024, 4, 8, 16)),
            author=cls.author,
        )
        cls.tender_during3.set_siae_found_list()
        cls.tender_during3.refresh_from_db()
        # add a siae interested
        TenderSiae.objects.create(
            tender=cls.tender_during3,
            siae=cls.siae1,
            detail_display_date=timezone.make_aware(timezone.datetime(2024, 4, 8, 17)),
            detail_contact_click_date=timezone.make_aware(timezone.datetime(2024, 4, 8, 18)),
        )

        # Tender no matching any siaes
        cls.tender_during4 = TenderFactory(
            presta_type=[siae_constants.PRESTA_DISP],
            sectors=[],
            is_country_area=False,
            first_sent_at=timezone.make_aware(timezone.datetime(2024, 4, 9, 6)),
            author=cls.author,
        )
        cls.tender_during4.set_siae_found_list()
        cls.tender_during4.refresh_from_db()

        cls.tender_after = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD],
            sectors=[cls.sector],
            is_country_area=True,
            first_sent_at=timezone.make_aware(timezone.datetime(2024, 4, 10, 10)),
            author=cls.author,
        )
        cls.tender_after.set_siae_found_list()
        cls.tender_after.refresh_from_db()

    @patch("lemarche.www.tenders.tasks.send_super_siaes_email_to_author")
    @patch("django.utils.timezone.now")
    def test_command_on_weekend(self, mock_now, mock_send_email):
        # Assume today is Sunday
        mock_now.return_value = timezone.make_aware(timezone.datetime(2024, 4, 7))

        out = StringIO()
        call_command("send_author_list_of_super_siaes_emails", stdout=out)

        self.assertIn("Weekend... Stopping. Come back on Monday :)", out.getvalue())
        self.assertNotIn("Step 1: Find Tender", out.getvalue())
        self.assertFalse(mock_send_email.called)

    @patch("lemarche.www.tenders.tasks.send_super_siaes_email_to_author")
    @patch("django.utils.timezone.now")
    def test_command_on_weekday(self, mock_now, mock_send_email):
        # Assume today is a weekday (e.g., Wednesday)
        mock_now.return_value = timezone.make_aware(timezone.datetime(2024, 4, 10, 7, 30))

        out = StringIO()
        call_command("send_author_list_of_super_siaes_emails", stdout=out)

        self.assertEqual(self.tender_before.siaes.count(), 3)

        output = out.getvalue()

        self.assertNotIn("Weekend... Stopping. Come back on Monday :)", output)
        self.assertIn("Step 1: Find Tender", output)
        self.assertIn("Step 2: send emails for each tender", output)
        self.assertIn("Found 3 Tender without siaes interested", output)

        self.assertIn(f"3 top siaes finded for #{self.tender_during1.id}", output)
        self.assertIn(f"3 top siaes finded for #{self.tender_during2.id}", output)
        self.assertIn(f"0 top siaes finded for #{self.tender_during4.id}", output)
        self.assertIn(f"Not enough siaes to send an email for #{self.tender_during4.id}", output)

        self.assertNotIn(f"top siaes finded for #{self.tender_before.id}", output)
        self.assertNotIn(f"top siaes finded for #{self.tender_during3.id}", output)  # with interested siae
        self.assertNotIn(f"top siaes finded for #{self.tender_after.id}", output)

        self.assertEqual(mock_send_email.call_count, 2)

    @patch("lemarche.www.tenders.tasks.send_super_siaes_email_to_author")
    @patch("django.utils.timezone.now")
    def test_command_on_weekday_dry_run(self, mock_now, mock_send_email):
        # Assume today is a weekday (e.g., Wednesday)
        mock_now.return_value = timezone.make_aware(timezone.datetime(2024, 4, 10, 7, 30))

        out = StringIO()
        call_command("send_author_list_of_super_siaes_emails", stdout=out, dry_run=True)

        output = out.getvalue()

        self.assertNotIn("Weekend... Stopping. Come back on Monday :)", output)
        self.assertIn("Step 1: Find Tender", output)
        self.assertIn("Step 2: display top siaes for each tender", output)
        self.assertIn("Found 3 Tender without siaes interested", output)
        self.assertNotIn("Email sent to tender author", output)

        mock_send_email.assert_not_called()


class UpdateTenderStatusToRejectedCommandTest(TestCase):
    def test_update_tender_status_to_rejected(self):
        """
        Test 'tenders_update_status_to_rejected' command.
        """
        recent_date = timezone.now() - timedelta(days=5)
        threshold_date = timezone.now() - timedelta(days=10)

        tender_recent = TenderFactory(
            status=Tender.StatusChoices.STATUS_DRAFT,
            email_sent_for_modification=True,
            logs=[
                {"action": "send tender author modification request", "date": recent_date.isoformat()},
            ],
        )

        tender_expired = TenderFactory(
            status=Tender.StatusChoices.STATUS_DRAFT,
            email_sent_for_modification=True,
            logs=[
                {"action": "send tender author modification request", "date": threshold_date.isoformat()},
            ],
        )

        tender_with_no_modification_request = TenderFactory(status=Tender.StatusChoices.STATUS_DRAFT)

        call_command("tenders_update_status_to_rejected", stdout=StringIO())

        tender_recent.refresh_from_db()
        tender_expired.refresh_from_db()
        tender_with_no_modification_request.refresh_from_db()

        self.assertEqual(tender_recent.status, Tender.StatusChoices.STATUS_DRAFT)
        self.assertEqual(tender_expired.status, Tender.StatusChoices.STATUS_REJECTED)
        self.assertEqual(tender_with_no_modification_request.status, Tender.StatusChoices.STATUS_DRAFT)


class UpdateTenderCountFieldsCommandTest(TestCase):
    @factory.django.mute_signals(signals.post_save, signals.m2m_changed)  # mute signals to avoid side effects
    def test_update_all_counters(self):
        """
        Create two tenders with siaes, and check that all count fields are updated correctly
        """
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()
        siae_3 = SiaeFactory()

        tender_1 = TenderFactory(siaes=[siae_1, siae_2, siae_3])

        TenderSiae.objects.create(
            tender=tender_1,
            siae=siae_1,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        TenderSiae.objects.create(
            tender=tender_1,
            siae=siae_2,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_not_interested_click_date=timezone.now(),
            detail_not_interested_feedback="test",
        )
        TenderSiae.objects.create(
            tender=tender_1,
            siae=siae_3,
            email_send_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )

        self.assertEqual(tender_1.siae_count, 0)
        self.assertEqual(tender_1.siae_email_send_count, 0)
        self.assertEqual(tender_1.siae_email_link_click_count, 0)
        self.assertEqual(tender_1.siae_detail_display_count, 0)
        self.assertEqual(tender_1.siae_detail_contact_click_count, 0)
        self.assertEqual(tender_1.siae_detail_not_interested_click_count, 0)
        self.assertEqual(tender_1.siae_email_link_click_or_detail_display_count, 0)

        std_out = StringIO()
        call_command("update_tender_count_fields", stdout=std_out)
        self.assertIn("Done! Processed 1 tenders", std_out.getvalue())

        tender_1.refresh_from_db()

        self.assertEqual(tender_1.siae_count, 3)
        self.assertEqual(tender_1.siae_email_send_count, 3)
        self.assertEqual(tender_1.siae_email_link_click_count, 2)
        self.assertEqual(tender_1.siae_detail_display_count, 2)
        self.assertEqual(tender_1.siae_detail_contact_click_count, 1)
        self.assertEqual(tender_1.siae_detail_not_interested_click_count, 1)
        self.assertEqual(tender_1.siae_email_link_click_or_detail_display_count, 3)

    @factory.django.mute_signals(signals.post_save, signals.m2m_changed)  # mute signals to avoid side effects
    def test_update_one_counter_future_deadline(self):
        """
        Create a tender with siaes and a future deadline, and check that the count fields are updated correctly
        """
        siae_1 = SiaeFactory()
        future_deadline = timezone.now() + timedelta(days=10)
        tender = TenderFactory(siaes=[siae_1], deadline_date=future_deadline)

        self.assertEqual(tender.siae_count, 0)

        std_out = StringIO()
        call_command("update_tender_count_fields", stdout=std_out)
        self.assertIn("Done! Processed 1 tenders", std_out.getvalue())

        tender.refresh_from_db()

        self.assertEqual(tender.siae_count, 1)

    @factory.django.mute_signals(signals.post_save, signals.m2m_changed)  # mute signals to avoid side effects
    def test_update_one_counter_outdated_deadline(self):
        """
        Create a tender with siaes and an outdated deadline, and check that the count fields are not updated
        """
        siae_1 = SiaeFactory()
        outdated_deadline = timezone.now() - timedelta(days=35)
        tender = TenderFactory(siaes=[siae_1], deadline_date=outdated_deadline)

        self.assertEqual(tender.siae_count, 0)

        std_out = StringIO()
        call_command("update_tender_count_fields", stdout=std_out)
        self.assertIn("Done! Processed 0 tenders", std_out.getvalue())

        tender.refresh_from_db()

        # Count should still be 0 as the tender has an outdated deadline
        self.assertEqual(tender.siae_count, 0)


class SiaeInterestReminderEmailCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create the email template needed by the command
        cls.email_template = TemplateTransactionalFactory(
            code="TENDERS_SIAE_INTERESTED_REMINDER_2D", is_active=True, brevo_id=1
        )

        # Create a buyer user
        cls.author = UserFactory(kind=User.KIND_BUYER)

        # Create a tender
        cls.tender = TenderFactory(author=cls.author, deadline_date=None)

        # Create SIAEs
        cls.siae1 = SiaeFactory(contact_email="siae1@example.com")
        cls.siae2 = SiaeFactory(contact_email="siae2@example.com")
        cls.siae3 = SiaeFactory(contact_email="siae3@example.com")

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch(
        "lemarche.www.tenders.tasks.whitelist_recipient_list",
        return_value=["siae1@example.com", "siae2@example.com", "siae3@example.com"],
    )
    @patch("django.utils.timezone.now")
    def test_send_siae_interested_reminder_email_weekday(self, mock_now, _mock_whitelist, mock_send_email):
        """Test the command on a weekday with TenderSiae that need reminders"""
        # Assume today is Wednesday
        now = timezone.make_aware(timezone.datetime(2025, 11, 12, 10, 0))
        mock_now.return_value = now

        # Create TenderSiae with detail_contact_click_date 2 days ago (should be reminded)
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae1,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=2, hours=1),
        )

        # Create TenderSiae with detail_contact_click_date 1 day ago (should NOT be reminded)
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae2,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=1, hours=1),
        )

        # Create TenderSiae with detail_contact_click_date 3 days ago (should NOT be reminded)
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae3,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=3, hours=1),
        )

        out = StringIO()
        call_command("send_siae_interested_reminder_emails", stdout=out)

        output = out.getvalue()

        # Check output
        self.assertNotIn("Weekend... Stopping. Come back on Monday :)", output)
        self.assertIn("Step 1: Find TenderSiae", output)
        self.assertIn("Step 2: Send emails for each tender", output)
        self.assertIn("Found 1 TenderSiaes to remind", output)
        self.assertIn(f"Tender {self.tender.id}: 1 TenderSiaes to remind", output)
        self.assertIn("Emails sent", output)

        # Verify that send_transactional_email was called once
        mock_send_email.assert_called_once()

        # Verify the call arguments
        call_args = mock_send_email.call_args
        self.assertIn("recipient_email", call_args.kwargs)
        self.assertIn("recipient_name", call_args.kwargs)
        self.assertIn("variables", call_args.kwargs)
        self.assertEqual(call_args.kwargs["recipient_email"], "siae1@example.com")

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch(
        "lemarche.www.tenders.tasks.whitelist_recipient_list",
        return_value=["siae1@example.com", "siae2@example.com", "siae3@example.com"],
    )
    @patch("django.utils.timezone.now")
    def test_send_siae_interested_reminder_email_weekend(self, mock_now, _mock_whitelist, mock_send_email):
        """Test the command on a weekend - should not send emails"""
        # Assume today is Saturday
        now = timezone.make_aware(timezone.datetime(2025, 11, 15, 10, 0))
        mock_now.return_value = now

        out = StringIO()
        call_command("send_siae_interested_reminder_emails", stdout=out)

        output = out.getvalue()

        # Check output
        self.assertIn("Weekend... Stopping. Come back on Monday :)", output)
        self.assertNotIn("Step 1: Find TenderSiae", output)

        # Verify that send_transactional_email was NOT called
        mock_send_email.assert_not_called()

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch(
        "lemarche.www.tenders.tasks.whitelist_recipient_list",
        return_value=["siae1@example.com", "siae2@example.com", "siae3@example.com"],
    )
    @patch("django.utils.timezone.now")
    def test_send_siae_interested_reminder_email_monday(self, mock_now, _mock_whitelist, mock_send_email):
        """Test the command on Monday - should account for weekend"""
        # Assume today is Monday
        now = timezone.make_aware(timezone.datetime(2025, 11, 17, 10, 0))
        mock_now.return_value = now

        # Create TenderSiae with detail_contact_click_date 4 days + 1 hour ago (Friday, should be reminded on Monday)
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae1,
            email_send_date=now - timedelta(days=6),
            detail_display_date=now - timedelta(days=5),
            detail_contact_click_date=now - timedelta(days=4),  # Friday
        )

        out = StringIO()
        call_command("send_siae_interested_reminder_emails", stdout=out)

        output = out.getvalue()

        # Check output
        self.assertNotIn("Weekend... Stopping. Come back on Monday :)", output)
        self.assertIn("Step 1: Find TenderSiae", output)
        self.assertIn("Found 1 TenderSiaes to remind", output)

        # Verify that send_transactional_email was called
        mock_send_email.assert_called_once()

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch(
        "lemarche.www.tenders.tasks.whitelist_recipient_list",
        return_value=["siae1@example.com", "siae2@example.com", "siae3@example.com"],
    )
    @patch("django.utils.timezone.now")
    def test_send_siae_interested_reminder_email_dry_run(self, mock_now, _mock_whitelist, mock_send_email):
        """Test the command with dry-run option - should not send emails"""
        # Assume today is Wednesday
        now = timezone.make_aware(timezone.datetime(2025, 11, 12, 10, 0))
        mock_now.return_value = now

        # Create TenderSiae with detail_contact_click_date 3 days + 1 hour ago
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae1,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=3),
        )

        out = StringIO()
        call_command("send_siae_interested_reminder_emails", "--dry-run", stdout=out)

        output = out.getvalue()

        # Check output
        self.assertIn("Step 1: Find TenderSiae", output)
        self.assertIn("Found 1 TenderSiaes to remind", output)
        self.assertNotIn("Step 2: Send emails for each tender", output)
        self.assertNotIn("Emails sent", output)

        # Verify that send_transactional_email was NOT called
        mock_send_email.assert_not_called()

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch(
        "lemarche.www.tenders.tasks.whitelist_recipient_list",
        return_value=["siae1@example.com", "siae2@example.com", "siae3@example.com"],
    )
    @patch("django.utils.timezone.now")
    def test_send_siae_interested_reminder_email_with_tender_id(self, mock_now, _mock_whitelist, mock_send_email):
        """Test the command with --tender-id option"""
        # Assume today is Wednesday
        now = timezone.make_aware(timezone.datetime(2025, 11, 12, 10, 0))
        mock_now.return_value = now

        # Create another tender
        tender2 = TenderFactory(author=self.author, deadline_date=None)

        # Create TenderSiae for first tender
        # Use 2 days + 1 hour ago to ensure it's strictly less than lt_days_ago (which is exactly 2 days ago)
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae1,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=2, hours=1),
        )

        # Create TenderSiae for second tender
        TenderSiaeFactory(
            tender=tender2,
            siae=self.siae2,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=2, hours=1),
        )

        out = StringIO()
        call_command("send_siae_interested_reminder_emails", "--tender-id", str(self.tender.id), stdout=out)

        output = out.getvalue()

        # Check output
        self.assertIn("Found 1 TenderSiaes to remind", output)
        self.assertIn(f"Tender {self.tender.id}: 1 TenderSiaes to remind", output)
        self.assertNotIn(f"Tender {tender2.id}", output)

        # Verify that send_transactional_email was called only once (for the specified tender)
        mock_send_email.assert_called_once()

    @patch("lemarche.conversations.models.TemplateTransactional.send_transactional_email")
    @patch(
        "lemarche.www.tenders.tasks.whitelist_recipient_list",
        return_value=["siae2@example.com"],
    )
    @patch("django.utils.timezone.now")
    def test_send_siae_interested_reminder_email_with_deadline(self, mock_now, _mock_whitelist, mock_send_email):
        """Test that tenders with past deadline are excluded"""
        # Assume today is Wednesday
        now = timezone.make_aware(timezone.datetime(2025, 11, 12, 10, 0))
        mock_now.return_value = now

        # Create tender with past deadline
        tender_past_deadline = TenderFactory(author=self.author, deadline_date=(now - timedelta(days=1)).date())

        # Create TenderSiae for tender with past deadline
        TenderSiaeFactory(
            tender=tender_past_deadline,
            siae=self.siae1,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=2, hours=1),
        )

        # Create TenderSiae for tender without deadline
        TenderSiaeFactory(
            tender=self.tender,
            siae=self.siae2,
            email_send_date=now - timedelta(days=5),
            detail_display_date=now - timedelta(days=4),
            detail_contact_click_date=now - timedelta(days=2, hours=1),
        )

        out = StringIO()
        call_command("send_siae_interested_reminder_emails", stdout=out)

        output = out.getvalue()

        # Check output - should only find the tender without deadline
        self.assertIn("Found 1 TenderSiaes to remind", output)
        self.assertIn(f"Tender {self.tender.id}: 1 TenderSiaes to remind", output)
        self.assertNotIn(f"Tender {tender_past_deadline.id}", output)

        # Verify that send_transactional_email was called only once
        mock_send_email.assert_called_once()

        # Verify the call arguments
        call_args = mock_send_email.call_args
        self.assertEqual(call_args.kwargs["recipient_email"], "siae2@example.com")
