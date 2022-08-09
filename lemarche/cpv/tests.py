from django.test import TestCase

from lemarche.cpv.factories import CodeFactory
from lemarche.cpv.models import Code


class CodeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        code = CodeFactory(name="Test", cpv_code="123")
        self.assertTrue("Test" in str(code))
        self.assertTrue("(123)" in str(code))


class CodeModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_error_if_cpv_code_too_long(self):
        code_too_long = Code(cpv_code="123456789")
        self.assertRaises(Exception, code_too_long.save)
