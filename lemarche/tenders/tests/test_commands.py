from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import factory
from django.core.management import call_command
from django.db.models import signals
from django.test import TestCase
from django.utils import timezone

from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class TestSendAuthorListOfSuperSiaesEmails(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()

        cls.siae1 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        siae1_activity = SiaeActivityFactory(
            siae=cls.siae1,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )
        siae1_activity.sectors.add(cls.sector)

        cls.siae2 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        siae2_activity = SiaeActivityFactory(
            siae=cls.siae2,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )
        siae2_activity.sectors.add(cls.sector)

        cls.siae3 = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        siae3_activity = SiaeActivityFactory(
            siae=cls.siae3,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )
        siae3_activity.sectors.add(cls.sector)

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
            status=tender_constants.STATUS_DRAFT,
            email_sent_for_modification=True,
            logs=[
                {"action": "send tender author modification request", "date": recent_date.isoformat()},
            ],
        )

        tender_expired = TenderFactory(
            status=tender_constants.STATUS_DRAFT,
            email_sent_for_modification=True,
            logs=[
                {"action": "send tender author modification request", "date": threshold_date.isoformat()},
            ],
        )

        tender_with_no_modification_request = TenderFactory(status=tender_constants.STATUS_DRAFT)

        call_command("tenders_update_status_to_rejected")

        tender_recent.refresh_from_db()
        tender_expired.refresh_from_db()
        tender_with_no_modification_request.refresh_from_db()

        self.assertEqual(tender_recent.status, tender_constants.STATUS_DRAFT)
        self.assertEqual(tender_expired.status, tender_constants.STATUS_REJECTED)
        self.assertEqual(tender_with_no_modification_request.status, tender_constants.STATUS_DRAFT)


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
        print(std_out.getvalue())
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
