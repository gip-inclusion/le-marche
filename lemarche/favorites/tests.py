from django.test import TestCase

from lemarche.favorites.factories import FavoriteListFactory
from lemarche.favorites.models import FavoriteList
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory


class FavoriteListModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        user = UserFactory()
        favorite_list = FavoriteListFactory(name="Ma liste", user=user)
        self.assertEqual(str(favorite_list), "Ma liste")


class FavoriteListModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_slug_field_on_save(self):
        user = UserFactory()
        favorite_list = FavoriteListFactory(name="Ma liste d'achat", user=user)
        self.assertTrue(favorite_list.slug.startswith("ma-liste-dachat-"))  # uuid4 at the end


class FavoriteListModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.siae_1 = SiaeFactory(name="ABC Insertion")
        cls.siae_2 = SiaeFactory(name="ZZ ESI")

    def test_favorite_list_item_ordering(self):
        favorite_list = FavoriteListFactory(user=self.user)
        favorite_list.siaes.add(self.siae_2)
        favorite_list.siaes.add(self.siae_1)
        # basic name ordering
        self.assertEqual(favorite_list.siaes.first(), self.siae_1)
        # -created_at ordering (added last shown first)
        self.assertEqual(favorite_list.favoriteitem_set.first().siae, self.siae_1)

    def test_with_siae_stats(self):
        favorite_list = FavoriteListFactory(user=self.user)
        favorite_list_with_siaes = FavoriteListFactory(user=self.user, siaes=[self.siae_1, self.siae_2])
        favorite_list_queryset = FavoriteList.objects.with_siae_stats()
        self.assertEqual(favorite_list_queryset.get(id=favorite_list.id).siae_count_annotated, 0)
        self.assertEqual(favorite_list_queryset.get(id=favorite_list_with_siaes.id).siae_count_annotated, 2)

    def test_siae_annotate_with_user_favorite_list_count(self):
        FavoriteListFactory(user=self.user, siaes=[self.siae_1])
        FavoriteListFactory(user=self.user, siaes=[self.siae_1])
        siae_queryset = Siae.objects.annotate_with_user_favorite_list_count(self.user)
        self.assertEqual(siae_queryset.get(id=self.siae_1.id).in_user_favorite_list_count, 2)
        self.assertEqual(siae_queryset.get(id=self.siae_2.id).in_user_favorite_list_count, 0)

    def test_siae_annotate_with_user_favorite_list_ids(self):
        favorite_list_1 = FavoriteListFactory(user=self.user, siaes=[self.siae_1])
        FavoriteListFactory(user=self.user, siaes=[self.siae_1])
        siae_queryset = Siae.objects.annotate_with_user_favorite_list_ids(self.user)
        self.assertEqual(len(siae_queryset.get(id=self.siae_1.id).in_user_favorite_list_ids), 2)
        self.assertEqual(len(siae_queryset.get(id=self.siae_2.id).in_user_favorite_list_ids), 0)
        self.assertEqual(siae_queryset.get(id=self.siae_1.id).in_user_favorite_list_ids[0], favorite_list_1.id)
