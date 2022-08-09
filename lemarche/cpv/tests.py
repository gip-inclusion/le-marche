from django.test import TestCase

from lemarche.cpv.factories import CodeFactory
from lemarche.cpv.models import Code


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
