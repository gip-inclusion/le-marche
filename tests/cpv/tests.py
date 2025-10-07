from django.test import TestCase

from lemarche.cpv.models import Code
from tests.cpv.factories import CodeFactory
from tests.sectors.factories import SectorFactory


class CodeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        code = CodeFactory(name="Test", cpv_code="11111111")
        self.assertTrue("Test" in str(code))
        self.assertTrue("(11111111)" in str(code))


class CodeModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_error_if_cpv_code_too_long(self):
        code_too_long = Code(cpv_code="123456789")
        self.assertRaises(Exception, code_too_long.save)

    def test_slug_field_on_save(self):
        code = CodeFactory(name="Un autre test", cpv_code="11111111")
        self.assertEqual(code.slug, "11111111-un-autre-test")

    def test_hierarchy_level_field_on_save(self):
        code = CodeFactory(name="Niveau 1", cpv_code="10000000")
        self.assertEqual(code.hierarchy_level, 1)
        code = CodeFactory(name="Niveau 1 again", cpv_code="11000000")
        self.assertEqual(code.hierarchy_level, 1)
        code = CodeFactory(name="Niveau 2", cpv_code="11200000")
        self.assertEqual(code.hierarchy_level, 2)
        code = CodeFactory(name="Niveau 7", cpv_code="11234567")
        self.assertEqual(code.hierarchy_level, 7)


class CodeModelQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()
        cls.code = CodeFactory()
        cls.code_with_sector = CodeFactory(sectors=[cls.sector])

    def test_has_sector(self):
        self.assertEqual(Code.objects.count(), 2)
        self.assertEqual(Code.objects.has_sector().count(), 1)

    def test_with_sector_stats(self):
        code_queryset = Code.objects.with_sector_stats()
        self.assertEqual(code_queryset.get(id=self.code.id).sector_count_annotated, 0)
        self.assertEqual(code_queryset.get(id=self.code_with_sector.id).sector_count_annotated, 1)
