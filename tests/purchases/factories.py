import factory
from factory.django import DjangoModelFactory

from lemarche.purchases.models import Purchase
from tests.companies.factories import CompanyFactory
from tests.siaes.factories import SiaeFactory


class PurchaseFactory(DjangoModelFactory):
    class Meta:
        model = Purchase

    supplier_name = factory.Sequence("Test Supplier {0}".format)
    supplier_siret = factory.Sequence("123456789012{0}".format)
    purchase_amount = factory.Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    purchase_year = factory.Faker("year")
    company = factory.SubFactory(CompanyFactory)
    siae = factory.SubFactory(SiaeFactory)
