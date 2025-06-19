from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


now = timezone.now()
date_tomorrow = now + timedelta(days=1)
old_date = timezone.now() - timedelta(days=91)
recent_date = now - timedelta(days=10)


class CrmBrevoSyncCompaniesCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Siae instances initialization"""
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_name = SiaeFactory(name="Test Company 1")
        cls.siae_with_user = SiaeFactory(users=[cls.user_siae])
        cls.siae_with_brevo_id = SiaeFactory(
            brevo_company_id="123456789",
            completion_rate=50,
        )

        cls.tender_1 = TenderFactory(deadline_date=date_tomorrow)
        cls.tender_2 = TenderFactory(deadline_date=date_tomorrow)

        TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_with_user,
            detail_contact_click_date=recent_date,
        )

        TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_with_brevo_id,
            email_send_date=recent_date,
            detail_contact_click_date=old_date,
        )

        cls.siae_with_user_stats = Siae.objects.with_tender_stats().filter(id=cls.siae_with_user.id).first()
        cls.siae_with_brevo_id_all_stats = (
            Siae.objects.with_tender_stats().filter(id=cls.siae_with_brevo_id.id).first()
        )
        cls.siae_with_brevo_id_recent_stats = (
            Siae.objects.with_tender_stats(since_days=90).filter(id=cls.siae_with_brevo_id.id).first()
        )

        # siae_with_brevo_id.extra_data initialization
        cls.siae_with_brevo_id.extra_data = {
            "brevo_company_data": {
                "completion_rate": (
                    cls.siae_with_brevo_id.completion_rate if cls.siae_with_brevo_id.completion_rate is not None else 0
                ),
                "tender_received": cls.siae_with_brevo_id_recent_stats.tender_email_send_count_annotated,
                "tender_interest": cls.siae_with_brevo_id_recent_stats.tender_detail_contact_click_count_annotated,
            }
        }
        cls.siae_with_brevo_id.save()
        cls.initial_extra_data = cls.siae_with_brevo_id.extra_data.copy()

    def test_annotated_fields_set_up(self):
        """Test annotated fields are correctly set up"""
        self.assertEqual(
            self.siae_with_user_stats.tender_email_send_count_annotated,
            0,
            "Le nombre total de besoins reçus devrait être 0",
        )
        self.assertEqual(
            self.siae_with_user_stats.tender_detail_contact_click_count_annotated,
            1,
            "Le nombre total de besoins intéressés devrait être 1",
        )
        self.assertEqual(
            self.siae_with_brevo_id_all_stats.tender_email_send_count_annotated,
            1,
            "Le nombre total de besoins reçus devrait être 1",
        )
        self.assertEqual(
            self.siae_with_brevo_id_all_stats.tender_detail_contact_click_count_annotated,
            1,
            "Le nombre total de besoins intéressés devrait être 1",
        )
        self.assertEqual(
            self.siae_with_brevo_id_recent_stats.tender_email_send_count_annotated,
            1,
            "Le nombre de besoins reçus dans les 90 derniers jours devrait être 1",
        )
        self.assertEqual(
            self.siae_with_brevo_id_recent_stats.tender_detail_contact_click_count_annotated,
            0,
            "Le nombre de besoins intéressés dans les 90 derniers jours devrait être 0",
        )

    @patch("lemarche.utils.apis.api_brevo.time.sleep")  # Mock sleep to speed up tests
    @patch("lemarche.utils.apis.api_brevo.BrevoCompanyApiClient")
    def test_new_siaes_are_synced_in_brevo(self, mock_client_class, mock_sleep):
        """Test new siaes are synced in brevo"""
        mock_client = mock_client_class.return_value
        call_command("crm_brevo_sync_companies", stdout=StringIO())

        # Only 2 SIAEs need sync: siae_with_name and siae_with_user
        # siae_with_brevo_id is skipped because it already has correct data in extra_data
        self.assertEqual(mock_client.create_or_update_company.call_count, 2)

    def test_siae_has_tender_stats(self):
        self.assertIsNotNone(
            self.siae_with_user_stats,
            "Cette SIAE devrait avoir des statistiques sur les besoins.",
        )
        self.assertIsNotNone(
            self.siae_with_brevo_id_all_stats,
            "Cette SIAE devrait avoir des statistiques sur les besoins.",
        )

    @patch("lemarche.utils.apis.api_brevo.time.sleep")  # Mock sleep to speed up tests
    def test_siae_extra_data_is_set_on_first_sync(self, mock_sleep):
        """
        - Test siae is updated if extra_data is changed.
        - Test siae.extra_data update does not erase existing data.
        """
        initial_extra_data = self.siae_with_user.extra_data.copy()
        initial_extra_data["test_data"] = "test value"

        self.siae_with_user.extra_data = initial_extra_data
        self.siae_with_user.save(update_fields=["extra_data"])

        call_command("crm_brevo_sync_companies", recently_updated=True, stdout=StringIO())

        self.siae_with_user.refresh_from_db()

        expected_extra_data = {
            "brevo_company_data": {
                "completion_rate": (
                    self.siae_with_user.completion_rate if self.siae_with_user.completion_rate is not None else 0
                ),
                "tender_received": self.siae_with_user_stats.tender_email_send_count_annotated,
                "tender_interest": self.siae_with_user_stats.tender_detail_contact_click_count_annotated,
            },
            "test_data": "test value",
        }

        self.assertNotEqual(initial_extra_data, expected_extra_data, "siae.extra_data aurait dû être mis à jour.")
        self.assertEqual(
            self.siae_with_user.extra_data, expected_extra_data, "siae.extra_data n'est pas conforme aux attentes."
        )

    @patch("lemarche.utils.apis.api_brevo.time.sleep")  # Mock sleep to speed up tests
    def test_siae_extra_data_is_not_updated_if_no_changes(self, mock_sleep):
        """Test siae.extra_data is not updated if no changes."""
        call_command("crm_brevo_sync_companies", recently_updated=True, stdout=StringIO())

        self.siae_with_brevo_id.refresh_from_db()
        self.assertEqual(
            self.initial_extra_data,
            self.siae_with_brevo_id.extra_data,
            "siae.extra_data a été mis à jour alors qu'il n'y avait pas de changement.",
        )

    @patch("lemarche.utils.apis.api_brevo.time.sleep")  # Mock sleep to speed up tests
    def test_fields_update_within_90_days_and_ignore_older_changes(self, mock_sleep):
        """Test fields update within 90 days and ignore older changes."""
        TenderSiae.objects.create(
            tender=self.tender_2,
            siae=self.siae_with_brevo_id,
            email_send_date=now,
            detail_contact_click_date=now,
        )

        call_command("crm_brevo_sync_companies", recently_updated=True, stdout=StringIO())

        self.siae_with_brevo_id_all_stats = (
            Siae.objects.with_tender_stats().filter(id=self.siae_with_brevo_id.id).first()
        )
        self.siae_with_brevo_id_recent_stats = (
            Siae.objects.with_tender_stats(since_days=90).filter(id=self.siae_with_brevo_id.id).first()
        )

        # Tender stats without date limit
        self.assertEqual(
            self.siae_with_brevo_id_all_stats.tender_email_send_count_annotated,
            2,
            "Le nombre total des besoins reçus devrait être 2",
        )
        self.assertEqual(
            self.siae_with_brevo_id_all_stats.tender_detail_contact_click_count_annotated,
            2,
            "Le nombre de bsoins interessés devrait être 2",
        )

        # Tender stats with date limit
        self.assertEqual(
            self.siae_with_brevo_id_recent_stats.tender_email_send_count_annotated,
            2,
            "Le nombre de besoins reçus dans les 90 jours devraient être 2",
        )
        self.assertEqual(
            self.siae_with_brevo_id_recent_stats.tender_detail_contact_click_count_annotated,
            1,
            "Les nombre de bsoins interessés dans les 90 jours devraient être 1",
        )

        expected_extra_data = {
            "brevo_company_data": {
                "completion_rate": (
                    self.siae_with_brevo_id.completion_rate
                    if self.siae_with_brevo_id.completion_rate is not None
                    else 0
                ),
                "tender_received": self.siae_with_brevo_id_recent_stats.tender_email_send_count_annotated,
                "tender_interest": self.siae_with_brevo_id_recent_stats.tender_detail_contact_click_count_annotated,
            }
        }

        self.assertNotEqual(
            self.initial_extra_data,
            expected_extra_data,
            "Les valeurs récentes dans extra_data devraient être mises à jour en fonction du filtre de 90 jours.",
        )
