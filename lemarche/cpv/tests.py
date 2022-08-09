from django.test import TestCase

from lemarche.cpv.factories import CodeFactory
from lemarche.cpv.models import Code
from lemarche.sectors.factories import SectorFactory


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


class CodeModelQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()
        cls.code = CodeFactory()
        cls.code_with_sector = CodeFactory(sectors=[cls.sector])

    def test_has_sector(self):
        self.assertEqual(Code.objects.count(), 2)
        self.assertEqual(Code.objects.has_sector().count(), 1)
