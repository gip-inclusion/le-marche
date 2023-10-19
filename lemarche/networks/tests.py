from django.test import TestCase

from lemarche.networks.factories import NetworkFactory
from lemarche.networks.models import Network
from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory


class NetworkModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.network = NetworkFactory(name="Mon réseau")

    def test_slug_field(self):
        self.assertEqual(self.network.slug, "mon-reseau")

    def test_str(self):
        self.assertEqual(str(self.network), "Mon réseau")


class NetworkQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory()
        cls.network = NetworkFactory()
        cls.network_with_user_partner = NetworkFactory()
        cls.network_with_siaes = NetworkFactory(siaes=[cls.siae_1, cls.siae_2])
        cls.user = UserFactory(partner_network=cls.network_with_user_partner)

    def test_with_siae_stats(self):
        network_queryset = Network.objects.with_siae_stats()
        self.assertEqual(network_queryset.get(id=self.network.id).siae_count_annotated, 0)
        self.assertEqual(network_queryset.get(id=self.network_with_siaes.id).siae_count_annotated, 2)

    def test_with_user_partner_stats(self):
        network_queryset = Network.objects.with_user_partner_stats()
        self.assertEqual(network_queryset.get(id=self.network.id).user_partner_count_annotated, 0)
        self.assertEqual(network_queryset.get(id=self.network_with_user_partner.id).user_partner_count_annotated, 1)
