from django.test import TestCase

from lemarche.networks.factories import NetworkFactory


class NetworkModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.network = NetworkFactory(name="Mon réseau")

    def test_slug_field(self):
        self.assertEqual(self.network.slug, "mon-reseau")

    def test_str(self):
        self.assertEqual(str(self.network), "Mon réseau")
