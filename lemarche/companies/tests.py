from django.test import TestCase

from lemarche.companies.factories import CompanyFactory
from lemarche.companies.models import Company
from lemarche.users.factories import UserFactory


class CompanyModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = CompanyFactory(name="Mon entreprise")

    def test_slug_field(self):
        self.assertEqual(self.company.slug, "mon-entreprise")

    def test_str(self):
        self.assertEqual(str(self.company), "Mon entreprise")


class CompanyQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = UserFactory()
        cls.user_2 = UserFactory()
        cls.company_with_users = CompanyFactory(users=[cls.user_1, cls.user_2])
        cls.company = CompanyFactory()

    def test_with_user_stats(self):
        company_queryset = Company.objects.with_user_stats()
        self.assertEqual(company_queryset.get(id=self.company.id).user_count_annotated, 0)
        self.assertEqual(company_queryset.get(id=self.company_with_users.id).user_count_annotated, 2)
