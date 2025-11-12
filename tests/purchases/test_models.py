from django.test import TestCase

from lemarche.purchases.models import Purchase
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from tests.companies.factories import CompanyFactory
from tests.purchases.factories import PurchaseFactory
from tests.users.factories import UserFactory


class PurchaseModelTest(TestCase):
    def test_purchase_get_purchase_for_user(self):
        # Test only user in right company can see his purchases
        company = CompanyFactory()
        user = UserFactory(company=company)
        purchases = PurchaseFactory.create_batch(5, company=company)
        PurchaseFactory()
        self.assertQuerySetEqual(Purchase.objects.get_purchase_for_user(user), purchases)

    def test_purchase_with_stats(self):
        # Test stats are correct
        # Create 5 purchases, 3 with different siae__kind and two without siae
        company = CompanyFactory()
        user = UserFactory(company=company)

        # Create purchases for insertion siae
        PurchaseFactory.create_batch(2, company=company, siae__kind=KIND_INSERTION_LIST[0], purchase_amount=25000)
        PurchaseFactory(
            company=company, siae__kind=KIND_INSERTION_LIST[1], purchase_amount=40000, purchase_category="Traiteur"
        )
        PurchaseFactory(
            company=company,
            siae__kind=KIND_INSERTION_LIST[1],
            purchase_amount=65000,
            buying_entity="USS Enterprise - Assurance",
        )

        # Create purchases for handicap siae
        PurchaseFactory.create_batch(2, company=company, siae__kind=KIND_HANDICAP_LIST[0], purchase_amount=20000)
        PurchaseFactory.create_batch(2, company=company, siae=None, purchase_amount=10000)

        # Create purchases for other company (not concerned by the stats)
        other_company = CompanyFactory()
        PurchaseFactory.create_batch(3, company=other_company, siae=None, purchase_amount=100000)
        PurchaseFactory(company=other_company, siae=None, purchase_amount=9000, purchase_category="Traiteur")
        PurchaseFactory(
            company=other_company, siae=None, purchase_amount=18000, buying_entity="USS Enterprise - Assurance"
        )

        stats = Purchase.objects.get_purchase_for_user(user).with_stats()
        self.assertEqual(stats["total_amount_annotated"], 215000)
        self.assertEqual(stats["total_inclusive_amount_annotated"], 195000)
        self.assertEqual(stats["total_insertion_amount_annotated"], 155000)
        self.assertEqual(stats["total_handicap_amount_annotated"], 40000)
        self.assertEqual(stats["total_suppliers_annotated"], 8)
        self.assertEqual(stats["total_inclusive_suppliers_annotated"], 6)
        self.assertEqual(stats[f"total_purchases_by_kind_{KIND_INSERTION_LIST[0]}"], 50000)
        self.assertEqual(stats[f"total_purchases_by_kind_{KIND_INSERTION_LIST[1]}"], 105000)
        self.assertEqual(stats[f"total_purchases_by_kind_{KIND_HANDICAP_LIST[0]}"], 40000)

        # count only purchases with siae__isnull=True
        self.assertEqual(stats["total_purchases_by_category_traiteur"], 40000)
        self.assertEqual(stats["total_purchases_by_buying_entity_uss-enterprise-assurance"], 65000)
