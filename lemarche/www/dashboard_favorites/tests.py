from django.test import TestCase
from django.urls import reverse

from lemarche.favorites.factories import FavoriteListFactory
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class DashboardFavoriteListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_favorite_list = UserFactory(kind=User.KIND_BUYER)
        cls.other_user_favorite_list = UserFactory(kind=User.KIND_PARTNER)
        # Additional data to check the correct prefetch
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()
        SiaeActivityFactory(
            siae=siae_1,
        )
        cls.favorite_list_1 = FavoriteListFactory(name="Liste 1", user=cls.user_favorite_list, siaes=[siae_1, siae_2])
        cls.favorite_list_2 = FavoriteListFactory(
            name="Liste 2", user=cls.other_user_favorite_list, siaes=[siae_1, siae_2]
        )

    def test_anonymous_user_cannot_view_favorite_list(self):
        url = reverse("dashboard_favorites:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))
        url = reverse("dashboard_favorites:list_detail", args=[self.favorite_list_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_favorite_list_user_can_view_favorite_list_detail(self):
        # non favorite list user
        self.client.force_login(self.other_user_favorite_list)
        url = reverse("dashboard_favorites:list_detail", args=[self.favorite_list_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")
        # favorite list user
        self.client.force_login(self.user_favorite_list)
        url = reverse("dashboard_favorites:list_detail", args=[self.favorite_list_1.slug])

        # check number of queries
        with self.assertNumQueries(10):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
