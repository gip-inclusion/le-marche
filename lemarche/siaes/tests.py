from django.test import TestCase

from lemarche.siaes.factories import SiaeFactory


class SiaeModelTest(TestCase):
    def setUp(self):
        SiaeFactory()

    def test_str(self):
        siae = SiaeFactory(name="Ma boite")
        self.assertEqual(str(siae), "Ma boite")
