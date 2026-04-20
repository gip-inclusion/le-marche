from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.siaes.utils import get_nudge_fields
from lemarche.users.models import User
from tests.siaes.factories import SiaeFactory
from tests.tenders.factories import TenderFactory
from tests.users.factories import UserFactory


class GetNudgeFieldsTest(TestCase):
    """Unit tests for get_nudge_fields() utility function."""

    def test_empty_contact_email_returns_field(self):
        siae = SiaeFactory(contact_email="")
        fields = get_nudge_fields(siae)
        field_names = [f["field"] for f in fields]
        self.assertIn("contact_email", field_names)

    def test_missing_ca_returns_field(self):
        siae = SiaeFactory(ca=None)
        fields = get_nudge_fields(siae)
        field_names = [f["field"] for f in fields]
        self.assertIn("ca", field_names)

    def test_stale_ca_returns_field(self):
        stale_date = timezone.now() - timedelta(days=400)
        siae = SiaeFactory(ca=100000, ca_last_updated=stale_date)
        fields = get_nudge_fields(siae)
        field_names = [f["field"] for f in fields]
        self.assertIn("ca", field_names)

    def test_recent_ca_not_returned(self):
        recent_date = timezone.now() - timedelta(days=10)
        siae = SiaeFactory(
            ca=100000,
            ca_last_updated=recent_date,
            contact_email="test@example.com",
            employees_insertion_count=5,
            employees_insertion_count_last_updated=recent_date,
            employees_permanent_count=3,
            employees_permanent_count_last_updated=recent_date,
        )
        fields = get_nudge_fields(siae)
        field_names = [f["field"] for f in fields]
        self.assertNotIn("ca", field_names)

    def test_max_five_fields_returned(self):
        siae = SiaeFactory(
            contact_email="",
            ca=None,
            employees_insertion_count=None,
            employees_permanent_count=None,
            sector_count=0,
            client_reference_count=0,
            label_count=0,
        )
        fields = get_nudge_fields(siae)
        self.assertLessEqual(len(fields), 5)

    def test_empty_field_is_inline(self):
        siae = SiaeFactory(ca=None)
        fields = get_nudge_fields(siae)
        ca_field = next((f for f in fields if f["field"] == "ca"), None)
        self.assertIsNotNone(ca_field)
        self.assertTrue(ca_field["inline"])

    def test_sector_field_is_not_inline(self):
        siae = SiaeFactory(
            contact_email="test@example.com",
            ca=100000,
            ca_last_updated=timezone.now(),
            employees_insertion_count=5,
            employees_insertion_count_last_updated=timezone.now(),
            employees_permanent_count=3,
            employees_permanent_count_last_updated=timezone.now(),
            sector_count=0,
        )
        fields = get_nudge_fields(siae)
        sectors_field = next((f for f in fields if f["field"] == "sectors"), None)
        if sectors_field:
            self.assertFalse(sectors_field["inline"])

    def test_complete_siae_returns_empty_list(self):
        recent_date = timezone.now() - timedelta(days=10)
        siae = SiaeFactory(
            contact_email="test@example.com",
            ca=100000,
            ca_last_updated=recent_date,
            employees_insertion_count=5,
            employees_insertion_count_last_updated=recent_date,
            employees_permanent_count=3,
            employees_permanent_count_last_updated=recent_date,
            sector_count=2,
            client_reference_count=1,
            label_count=1,
        )
        fields = get_nudge_fields(siae)
        self.assertEqual(len(fields), 0)


class ShouldShowNudgeTest(TestCase):
    """Unit tests for Siae.should_show_nudge()."""

    def test_null_nudge_last_seen_returns_true_when_fields_incomplete(self):
        siae = SiaeFactory(ca=None, nudge_last_seen_at=None)
        self.assertTrue(siae.should_show_nudge())

    def test_recent_nudge_last_seen_returns_false(self):
        siae = SiaeFactory(ca=None, nudge_last_seen_at=timezone.now() - timedelta(days=10))
        self.assertFalse(siae.should_show_nudge())

    def test_old_nudge_last_seen_returns_true_when_fields_incomplete(self):
        siae = SiaeFactory(ca=None, nudge_last_seen_at=timezone.now() - timedelta(days=35))
        self.assertTrue(siae.should_show_nudge())

    def test_complete_siae_returns_false_even_if_never_seen(self):
        recent_date = timezone.now() - timedelta(days=10)
        siae = SiaeFactory(
            contact_email="test@example.com",
            ca=100000,
            ca_last_updated=recent_date,
            employees_insertion_count=5,
            employees_insertion_count_last_updated=recent_date,
            employees_permanent_count=3,
            employees_permanent_count_last_updated=recent_date,
            sector_count=2,
            client_reference_count=1,
            label_count=1,
            nudge_last_seen_at=None,
        )
        self.assertFalse(siae.should_show_nudge())


class TenderSiaeNudgeDismissViewTest(TestCase):
    """Tests for TenderSiaeNudgeDismissView."""

    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(ca=None, nudge_last_seen_at=None)
        cls.user = UserFactory(kind=User.KIND_SIAE)
        cls.user.siaes.add(cls.siae)
        cls.tender = TenderFactory()
        cls.url = reverse("tenders:nudge-dismiss", kwargs={"slug": cls.tender.slug})

    def test_unauthenticated_redirects(self):
        response = self.client.post(self.url, {"siae_slug": self.siae.slug})
        self.assertEqual(response.status_code, 302)

    def test_wrong_ownership_returns_403(self):
        other_user = UserFactory(kind=User.KIND_SIAE)
        self.client.force_login(other_user)
        response = self.client.post(self.url, {"siae_slug": self.siae.slug})
        self.assertEqual(response.status_code, 403)

    def test_valid_dismiss_updates_nudge_last_seen_at(self):
        self.client.force_login(self.user)
        self.assertIsNone(self.siae.nudge_last_seen_at)
        response = self.client.post(self.url, {"siae_slug": self.siae.slug})
        self.assertEqual(response.status_code, 200)
        self.siae.refresh_from_db()
        self.assertIsNotNone(self.siae.nudge_last_seen_at)

    def test_valid_dismiss_returns_empty_response(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"siae_slug": self.siae.slug})
        self.assertEqual(response.content, b"")


class TenderSiaeNudgeUpdateViewTest(TestCase):
    """Tests for TenderSiaeNudgeUpdateView."""

    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(ca=None, nudge_last_seen_at=None)
        cls.user = UserFactory(kind=User.KIND_SIAE)
        cls.user.siaes.add(cls.siae)
        cls.tender = TenderFactory()
        cls.url = reverse("tenders:nudge-update-field", kwargs={"slug": cls.tender.slug})

    def _post_data(self, field_name, field_value, step_index=0, total_steps=1):
        return {
            "siae_slug": self.siae.slug,
            "field_name": field_name,
            "field_value": field_value,
            "step_index": step_index,
            "total_steps": total_steps,
        }

    def test_unauthenticated_redirects(self):
        response = self.client.post(self.url, self._post_data("ca", "50000"))
        self.assertEqual(response.status_code, 302)

    def test_wrong_ownership_returns_403(self):
        other_user = UserFactory(kind=User.KIND_SIAE)
        self.client.force_login(other_user)
        response = self.client.post(self.url, self._post_data("ca", "50000"))
        self.assertEqual(response.status_code, 403)

    def test_valid_ca_update_saves_to_db(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self._post_data("ca", "75000", step_index=0, total_steps=1))
        self.assertEqual(response.status_code, 200)
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.ca, 75000)

    def test_invalid_negative_ca_returns_error_fragment(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self._post_data("ca", "-500"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nombre entier positif")
        self.siae.refresh_from_db()
        self.assertIsNone(self.siae.ca)

    def test_last_step_sets_nudge_last_seen_at(self):
        self.client.force_login(self.user)
        self.assertIsNone(self.siae.nudge_last_seen_at)
        self.client.post(self.url, self._post_data("ca", "100000", step_index=0, total_steps=1))
        self.siae.refresh_from_db()
        self.assertIsNotNone(self.siae.nudge_last_seen_at)

    def test_confirmation_message_on_last_step(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self._post_data("ca", "100000", step_index=0, total_steps=1))
        self.assertContains(response, "Merci")

    def test_invalid_email_returns_error_fragment(self):
        siae = SiaeFactory(contact_email="", nudge_last_seen_at=None)
        self.user.siaes.add(siae)
        self.client.force_login(self.user)
        url = reverse("tenders:nudge-update-field", kwargs={"slug": self.tender.slug})
        response = self.client.post(
            url,
            {
                "siae_slug": siae.slug,
                "field_name": "contact_email",
                "field_value": "not-an-email",
                "step_index": 0,
                "total_steps": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "e-mail valide")
