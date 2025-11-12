from django.test import TestCase
from django.utils import timezone

from tests.siaes.factories import SiaeFactory, SiaeUserRequestFactory
from tests.users.factories import UserFactory


class SiaeUserRequestActionsTest(TestCase):
    def setUp(self):
        self.siae = SiaeFactory(brevo_company_id="BREVO123")
        self.admin_user = UserFactory()
        self.assignee = UserFactory()
        self.siae.users.add(self.assignee)
        self.siae_user_request = SiaeUserRequestFactory(
            siae=self.siae,
            initiator=UserFactory(),
            assignee=self.assignee,
            logs=[],
        )

    def test_approve_pending_request(self):
        result = self.siae_user_request.approve(actor=self.admin_user)
        self.assertTrue(result)

        self.siae_user_request.refresh_from_db()
        self.assertTrue(self.siae_user_request.response)
        self.assertIsNotNone(self.siae_user_request.response_date)
        self.assertTrue(self.siae.users.filter(pk=self.siae_user_request.initiator.pk).exists())

        last_log = self.siae_user_request.logs[-1]
        self.assertEqual(last_log["action"], "response_true")
        self.assertEqual(last_log.get("actor"), f"#{self.admin_user.id} {self.admin_user.full_name}")

    def test_approve_request_already_processed(self):
        self.siae_user_request.response = True
        self.siae_user_request.response_date = timezone.now()
        self.siae_user_request.save(update_fields=["response", "response_date"])

        result = self.siae_user_request.approve(actor=self.admin_user)
        self.assertFalse(result)

    def test_reject_pending_request(self):
        result = self.siae_user_request.reject(actor=self.admin_user)
        self.assertTrue(result)

        self.siae_user_request.refresh_from_db()
        self.assertFalse(self.siae_user_request.response)
        self.assertIsNotNone(self.siae_user_request.response_date)
        self.assertFalse(self.siae.users.filter(pk=self.siae_user_request.initiator.pk).exists())

        last_log = self.siae_user_request.logs[-1]
        self.assertEqual(last_log["action"], "response_false")
        self.assertEqual(last_log.get("actor"), f"#{self.admin_user.id} {self.admin_user.full_name}")

    def test_reject_request_already_processed(self):
        self.siae_user_request.response = False
        self.siae_user_request.response_date = timezone.now()
        self.siae_user_request.save(update_fields=["response", "response_date"])

        result = self.siae_user_request.reject(actor=self.admin_user)
        self.assertFalse(result)

    def test_reject_request_already_accepted(self):
        self.siae_user_request.approve(actor=self.admin_user)
        self.siae_user_request.refresh_from_db()
        self.assertTrue(self.siae_user_request.response)
        self.assertIsNotNone(self.siae_user_request.response_date)
        self.assertTrue(self.siae.users.filter(pk=self.siae_user_request.initiator.pk).exists())

        result = self.siae_user_request.reject(actor=self.admin_user)
        self.assertTrue(result)
        self.assertFalse(self.siae.users.filter(pk=self.siae_user_request.initiator.pk).exists())
