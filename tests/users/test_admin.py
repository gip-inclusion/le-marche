from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from tests.users.factories import UserFactory


@patch("lemarche.users.models.notify_user_onboarded")
class UserAdminOnboardUserViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = UserFactory(is_staff=True)
        cls.staff_user_with_permission = UserFactory(is_staff=True)
        cls.staff_user_with_permission.user_permissions.add(
            Permission.objects.get(codename="change_user", content_type__app_label="users")
        )

    def setUp(self):
        self.user = UserFactory(have_followed_onboarding=False)
        self.url = reverse("admin:onboard_user", args=[self.user.pk])

    def test_get_is_not_allowed(self, mock_notify):
        self.client.force_login(self.staff_user_with_permission)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.user.refresh_from_db()
        self.assertFalse(self.user.have_followed_onboarding)
        mock_notify.assert_not_called()

    def test_staff_user_without_change_permission_cannot_onboard_user(self, mock_notify):
        self.client.force_login(self.staff_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertFalse(self.user.have_followed_onboarding)
        mock_notify.assert_not_called()

    def test_staff_user_with_change_permission_can_onboard_user(self, mock_notify):
        self.client.force_login(self.staff_user_with_permission)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:users_user_change", args=[self.user.pk]))
        self.user.refresh_from_db()
        self.assertTrue(self.user.have_followed_onboarding)
        mock_notify.assert_called_once()
