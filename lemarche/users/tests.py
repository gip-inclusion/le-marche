from django.test import TestCase

from lemarche.companies.factories import CompanyFactory
from lemarche.favorites.factories import FavoriteListFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users import constants as user_constants
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_str(self):
        user = UserFactory(email="coucou@example.com")
        self.assertEqual(str(user), "coucou@example.com")

    def test_full_name(self):
        user = UserFactory(first_name="Paul", last_name="Anploi")
        self.assertEqual(user.full_name, "Paul Anploi")

    def test_kind_detail_display(self):
        user_siae = UserFactory(kind=user_constants.KIND_SIAE)
        user_buyer = UserFactory(kind=user_constants.KIND_BUYER)
        user_buyer_public = UserFactory(kind=user_constants.KIND_BUYER, buyer_kind=user_constants.BUYER_KIND_PUBLIC)
        user_buyer_private_pme = UserFactory(
            kind=user_constants.KIND_BUYER,
            buyer_kind=user_constants.BUYER_KIND_PRIVATE,
            buyer_kind_detail=user_constants.BUYER_KIND_DETAIL_PRIVATE_PME,
        )
        user_partner = UserFactory(kind=user_constants.KIND_PARTNER)
        user_partner_facilitator = UserFactory(
            kind=user_constants.KIND_PARTNER, partner_kind=user_constants.PARTNER_KIND_FACILITATOR
        )
        self.assertEqual(user_siae.kind_detail_display, "Structure")
        self.assertEqual(user_buyer.kind_detail_display, "Acheteur")
        self.assertEqual(user_partner.kind_detail_display, "Partenaire")
        self.assertEqual(user_buyer_public.kind_detail_display, "Acheteur")
        self.assertEqual(user_buyer_private_pme.kind_detail_display, "Acheteur : PME")
        self.assertEqual(
            user_partner_facilitator.kind_detail_display, "Partenaire : Facilitateur des clauses sociales"
        )


class UserModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_is_admin_bizdev(self):
        UserFactory(kind=user_constants.KIND_ADMIN, is_staff=True)
        UserFactory(kind=user_constants.KIND_ADMIN, is_staff=True, position="BizDev")
        UserFactory(kind=user_constants.KIND_ADMIN, is_staff=True, position="Bizdev")
        self.assertEqual(User.objects.count(), 1 + 3)
        self.assertEqual(User.objects.is_admin_bizdev().count(), 2)

    def test_has_company(self):
        user_2 = UserFactory()
        CompanyFactory(users=[user_2])
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_company().count(), 1)

    def test_has_siae(self):
        user_2 = UserFactory()
        SiaeFactory(users=[user_2])
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_siae().count(), 1)

    def test_has_tender(self):
        user_2 = UserFactory()
        TenderFactory(author=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_tender().count(), 1)

    def test_has_favorite_list(self):
        user_2 = UserFactory()
        FavoriteListFactory(user=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_favorite_list().count(), 1)

    def test_has_api_key(self):
        UserFactory(api_key="coucou")
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_api_key().count(), 1)

    def test_has_email_domain(self):
        UserFactory(email="test@ain.fr")
        UserFactory(email="test@plateau-urbain.fr")
        self.assertEqual(User.objects.count(), 1 + 2)
        for EMAIL_DOMAIN in ["ain.fr", "@ain.fr"]:
            with self.subTest(email_domain=EMAIL_DOMAIN):
                self.assertEqual(User.objects.has_email_domain(email_domain=EMAIL_DOMAIN).count(), 1)

    def test_with_siae_stats(self):
        user_2 = UserFactory()
        SiaeFactory(users=[user_2])
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.with_siae_stats().filter(id=self.user.id).first().siae_count_annotated, 0)
        self.assertEqual(User.objects.with_siae_stats().filter(id=user_2.id).first().siae_count_annotated, 1)

    def test_with_tender_stats(self):
        user_2 = UserFactory()
        TenderFactory(author=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.with_tender_stats().filter(id=self.user.id).first().tender_count_annotated, 0)
        self.assertEqual(User.objects.with_tender_stats().filter(id=user_2.id).first().tender_count_annotated, 1)

    def test_chain_querysets(self):
        user_2 = UserFactory(api_key="chain")
        siae = SiaeFactory()
        siae.users.add(user_2)
        self.assertEqual(
            User.objects.has_api_key().with_siae_stats().filter(id=user_2.id).first().siae_count_annotated, 1
        )


class UserModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_update_last_updated_fields(self):
        user = UserFactory()
        self.assertIsNone(user.api_key)
        self.assertIsNone(user.api_key_last_updated)
        # new value: last_updated field will be set
        user = User.objects.get(id=user.id)  # we need to fetch it again to pass through the __init__
        user.api_key = "AZERTY"
        user.save()
        self.assertEqual(user.api_key, "AZERTY")
        self.assertIsNotNone(user.api_key_last_updated)
        api_key_last_updated = user.api_key_last_updated
        # same value: last_updated field will not be updated
        user = User.objects.get(id=user.id)
        user.api_key = "AZERTY"
        user.save()
        self.assertEqual(user.api_key, "AZERTY")
        self.assertEqual(user.api_key_last_updated, api_key_last_updated)
        # updated value: last_updated field will be updated
        user = User.objects.get(id=user.id)
        user.api_key = "QWERTY"
        user.save()
        self.assertEqual(user.api_key, "QWERTY")
        self.assertNotEqual(user.api_key_last_updated, api_key_last_updated)

    def test_update_related_favorite_list_count_on_save(self):
        user = UserFactory()
        self.assertEqual(user.favorite_list_count, 0)
        # create 2 lists
        FavoriteListFactory(user=user)
        FavoriteListFactory(user=user)
        self.assertEqual(user.favorite_lists.count(), 2)
        self.assertEqual(user.favorite_list_count, 2)
        # delete 1 list
        user.favorite_lists.first().delete()
        self.assertEqual(user.favorite_lists.count(), 1)
        self.assertEqual(user.favorite_list_count, 1)
