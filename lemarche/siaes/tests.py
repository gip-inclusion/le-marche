from django.test import TestCase

from lemarche.siaes.models import Siae, SiaeLabel, SiaeOffer


class SiaeLabelModelTest(TestCase):
    def setUp(self):
        Siae.objects.create()

    def test_spacetime_continuum(self):
        self.assertEqual(1, 1)
