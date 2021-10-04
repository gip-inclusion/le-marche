from django.test import TestCase

from lemarche.networks.factories import NetworkFactory


class NetworkModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        network = NetworkFactory(name="Mon réseau")
        self.assertEqual(str(network), "Mon réseau")
