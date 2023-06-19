from django.test import TestCase

from lemarche.companies.factories import CompanyFactory


class CompanyModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = CompanyFactory(name="Mon entreprise")

    def test_slug_field(self):
        self.assertEqual(self.company.slug, "mon-entreprise")

    def test_str(self):
        self.assertEqual(str(self.company), "Mon entreprise")
