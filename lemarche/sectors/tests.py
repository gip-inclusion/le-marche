from django.test import TestCase

from lemarche.sectors.factories import SectorFactory, SectorGroupFactory


class NetworkModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector_group = SectorGroupFactory(name="Un groupe")
        cls.sector = SectorFactory(name="Un secteur", group=cls.sector_group)
        cls.sector_other = SectorFactory(name="Autre", group=cls.sector_group)

    def test_slug_field(self):
        self.assertEqual(self.sector.slug, "un-secteur")
        self.assertEqual(self.sector_other.slug, "autre-un-groupe")

    def test_str(self):
        self.assertEqual(str(self.sector), "Un secteur")
