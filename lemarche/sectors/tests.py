from django.test import TestCase

from lemarche.sectors.factories import SectorFactory, SectorGroupFactory
from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes.factories import SiaeFactory


class SectorGroupModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector_group = SectorGroupFactory(name="Un groupe")

    def test_slug_field(self):
        self.assertEqual(self.sector_group.slug, "un-groupe")

    def test_str(self):
        self.assertEqual(str(self.sector_group), "Un groupe")


class SectorGroupQuerysetModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector_group = SectorGroupFactory(name="Informatique")
        cls.sector_group_with_sectors = SectorGroupFactory(name="Bricolage")
        SectorFactory(name="Développement de logiciel", group=cls.sector_group_1)
        SectorFactory(name="Dépannage informatique", group=cls.sector_group_1)

    def with_sector_stats(self):
        sector_group_queryset = SectorGroup.objects.with_user_stats()
        self.assertEqual(sector_group_queryset.get(id=self.sector_group.id).sector_count_annotated, 0)
        self.assertEqual(sector_group_queryset.get(id=self.sector_group_with_sectors.id).sector_count_annotated, 2)


class SectorModelTest(TestCase):
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


class SectorQuerysetModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory()
        cls.sector_group_1 = SectorGroupFactory(name="Informatique")
        cls.sector_group_2 = SectorGroupFactory(name="Bricolage")
        cls.sector_1_1 = SectorFactory(name="Développement de logiciel", group=cls.sector_group_1)
        cls.sector_1_2 = SectorFactory(name="Dépannage informatique", group=cls.sector_group_1)
        cls.sector_1_3 = SectorFactory(name="Autre", group=cls.sector_group_1)
        cls.sector_2_1 = SectorFactory(name="Plomberie", group=cls.sector_group_2)
        cls.sector_2_2 = SectorFactory(name="Autre (Bricolage)", group=cls.sector_group_2)
        cls.sector_3 = SectorFactory(name="Un secteur seul", group=None, siaes=[cls.siae_1, cls.siae_2])

    def test_form_filter_queryset(self):
        sectors = Sector.objects.form_filter_queryset()
        # remove sectors without groups
        self.assertEqual(sectors.count(), 3 + 2)
        # order by group id
        self.assertEqual(sectors[0].group, self.sector_group_1)
        # and then by name (but with Autre at the end)
        self.assertEqual(sectors[0], self.sector_1_2)
        self.assertEqual(sectors[2], self.sector_1_3)
        self.assertEqual(sectors[4], self.sector_2_2)

    def test_with_siae_stats(self):
        sector_queryset = Sector.objects.with_siae_stats()
        self.assertEqual(sector_queryset.get(id=self.sector_1_1.id).siae_count_annotated, 0)
        self.assertEqual(sector_queryset.get(id=self.sector_3.id).siae_count_annotated, 2)
