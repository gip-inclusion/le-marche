from django.test import TestCase

from lemarche.favorites.factories import FavoriteListFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users.factories import UserFactory
from lemarche.users.models import User
from lemarche.utils import constants


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
        user_siae = UserFactory(kind=constants.USER_KIND_SIAE)
        user_buyer = UserFactory(kind=constants.USER_KIND_BUYER)
        user_buyer_public = UserFactory(kind=constants.USER_KIND_BUYER, buyer_kind=User.BUYER_KIND_PUBLIC)
        user_buyer_private_pme = UserFactory(
            kind=constants.USER_KIND_BUYER,
            buyer_kind=User.BUYER_KIND_PRIVATE,
            buyer_kind_detail=User.BUYER_KIND_DETAIL_PRIVATE_PME,
        )
        user_partner = UserFactory(kind=constants.USER_KIND_PARTNER)
        user_partner_facilitator = UserFactory(
            kind=constants.USER_KIND_PARTNER, partner_kind=User.PARTNER_KIND_FACILITATOR
        )
        self.assertEqual(user_siae.kind_detail_display, "Structure")
        self.assertEqual(user_buyer.kind_detail_display, "Acheteur")
        self.assertEqual(user_partner.kind_detail_display, "Partenaire")
        self.assertEqual(user_buyer_public.kind_detail_display, "Acheteur")
        self.assertEqual(user_buyer_private_pme.kind_detail_display, "Acheteur : Privé : PME")
        self.assertEqual(
            user_partner_facilitator.kind_detail_display, "Partenaire : Facilitateur des clauses sociales"
        )


class UserModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_has_siae_queryset(self):
        user_2 = UserFactory()
        siae = SiaeFactory()
        siae.users.add(user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_siae().count(), 1)

    def test_has_tender_queryset(self):
        user_2 = UserFactory()
        TenderFactory(author=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_tender().count(), 1)

    def test_has_favorite_list_queryset(self):
        user_2 = UserFactory()
        FavoriteListFactory(user=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_favorite_list().count(), 1)

    def test_has_api_key_queryset(self):
        UserFactory(api_key="coucou")
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.has_api_key().count(), 1)

    def test_with_siae_stats_queryset(self):
        user_2 = UserFactory()
        siae = SiaeFactory()
        siae.users.add(user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.with_siae_stats().filter(id=self.user.id).first().siae_count, 0)
        self.assertEqual(User.objects.with_siae_stats().filter(id=user_2.id).first().siae_count, 1)

    def test_with_tender_stats_queryset(self):
        user_2 = UserFactory()
        TenderFactory(author=user_2)
        self.assertEqual(User.objects.count(), 1 + 1)
        self.assertEqual(User.objects.with_tender_stats().filter(id=self.user.id).first().tender_count, 0)
        self.assertEqual(User.objects.with_tender_stats().filter(id=user_2.id).first().tender_count, 1)

    def test_chain_querysets(self):
        user_2 = UserFactory(api_key="chain")
        siae = SiaeFactory()
        siae.users.add(user_2)
        self.assertEqual(User.objects.has_api_key().with_siae_stats().filter(id=user_2.id).first().siae_count, 1)


class UserModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_update_last_updated_fields(self):
        user = UserFactory()
        self.assertEqual(user.api_key, None)
        self.assertEqual(user.api_key_last_updated, None)
        # new value: last_updated field will be set
        user = User.objects.get(id=user.id)  # we need to fetch it again to pass through the __init__
        user.api_key = "AZERTY"
        user.save()
        self.assertEqual(user.api_key, "AZERTY")
        self.assertNotEqual(user.api_key_last_updated, None)
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
