from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
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
