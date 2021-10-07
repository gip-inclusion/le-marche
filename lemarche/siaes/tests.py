from django.test import TestCase

from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory


class SiaeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        siae = SiaeFactory(name="Ma boite")
        self.assertEqual(str(siae), "Ma boite")

    def test_is_live_queryset(self):
        SiaeFactory(is_active=True, is_delisted=True)
        SiaeFactory(is_active=False, is_delisted=True)
        SiaeFactory(is_active=True, is_delisted=False)  # live
        SiaeFactory(is_active=False, is_delisted=False)
        self.assertEqual(Siae.objects.count(), 4)
        self.assertEqual(Siae.objects.is_live().count(), 1)
        self.assertEqual(Siae.objects.is_not_live().count(), 3)

    def test_has_user_queryset(self):
        SiaeFactory()
        siae = SiaeFactory()
        user = UserFactory()
        siae.users.add(user)
        self.assertEqual(Siae.objects.count(), 2)
        self.assertEqual(Siae.objects.has_user().count(), 1)
