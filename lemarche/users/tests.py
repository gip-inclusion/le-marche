from django.test import TestCase

from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class UserModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        user = UserFactory(email="coucou@domain.com")
        self.assertEqual(str(user), "coucou@domain.com")

    def test_full_name(self):
        user = UserFactory(first_name="Paul", last_name="Anploi")
        self.assertEqual(user.full_name, "Paul Anploi")

    def test_siae_admins_queryset(self):
        UserFactory()
        user = UserFactory()
        siae = SiaeFactory()
        siae.users.add(user)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.siae_admins().count(), 1)

    def test_with_api_key_queryset(self):
        UserFactory()
        UserFactory(api_key="coucou")
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.with_api_key().count(), 1)
