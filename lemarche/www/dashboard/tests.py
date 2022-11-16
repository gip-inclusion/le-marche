from django.test import TestCase
from django.urls import reverse

from lemarche.favorites.factories import FavoriteListFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import SiaeUser
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class DashboardHomeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_with_api_token = UserFactory(kind=User.KIND_BUYER, api_key="admin")
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)

    def test_anonymous_user_cannot_access_profile(self):
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/profil/")

    def test_user_can_access_profile(self):
        self.client.force_login(self.user)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_buyer_should_display_custom_dashboard(self):
        self.client.force_login(self.user_buyer)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mes besoins")
        self.assertContains(response, "M'informer sur le marché")
        self.assertContains(response, "Annuaire des facilitateurs")
        self.assertContains(response, "Valoriser mes achats")
        self.assertContains(response, "API")
        self.assertContains(response, "M'informer sur les achats inclusifs")
        self.assertNotContains(response, "Ajouter une structure")

    def test_user_siae_should_display_custom_dashboard(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ajouter une structure")
        self.assertContains(response, "Les opportunités du marché")
        self.assertContains(response, "Solutions et ressources")
        self.assertContains(response, "Aides-territoires")
        self.assertNotContains(response, "Mes besoins")
        # self.assertNotContains(response, "API")

    def test_user_with_api_key_should_see_api_token(self):
        self.client.force_login(self.user_buyer_with_api_token)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Votre token")

    def test_viewing_dashboard_should_update_stats(self):
        self.assertIsNone(self.user.dashboard_last_seen_date)
        self.client.force_login(self.user)
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(id=self.user.id).dashboard_last_seen_date)


class DashboardSiaeSearchAdoptViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_siae_2 = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.user_admin = UserFactory(kind=User.KIND_ADMIN)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)
        cls.siae_without_user = SiaeFactory()

    def test_anonymous_user_cannot_adopt_siae(self):
        url = reverse("dashboard:siae_search_by_siret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_siae_user_or_admin_can_adopt_siae(self):
        ALLOWED_USERS = [self.user_siae, self.user_admin]
        for user in ALLOWED_USERS:
            self.client.force_login(user)
            url = reverse("dashboard:siae_search_by_siret")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        NOT_ALLOWED_USERS = [self.user_buyer, self.user_partner]
        for user in NOT_ALLOWED_USERS:
            self.client.force_login(user)
            url = reverse("dashboard:siae_search_by_siret")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")

    def test_only_siaes_without_users_can_be_adopted(self):
        self.client.force_login(self.user_siae)

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_only_new_siae_user_can_adopt_confirm(self):
        self.client.force_login(self.user_siae)
        self.assertEqual(self.siae_with_user.users.count(), 1)
        self.assertEqual(self.user_siae.siaes.count(), 1)  # setUpTestData

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_siae_without_user_adopt_confirm(self):
        self.client.force_login(self.user_siae)
        self.assertEqual(self.siae_without_user.users.count(), 0)
        self.assertEqual(self.user_siae.siaes.count(), 1)  # setUpTestData

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Je confirme")

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.post(url)  # data={}
        self.assertEqual(response.status_code, 302)  # redirect to success_url
        self.assertEqual(response.url, f"/profil/prestataires/{self.siae_without_user.slug}/modifier/")
        self.assertEqual(self.siae_without_user.users.count(), 1)
        self.assertEqual(self.user_siae.siaes.count(), 1 + 1)

    def test_siae_with_existing_user_adopt_confirm(self):
        self.client.force_login(self.user_siae_2)
        self.assertEqual(self.siae_with_user.users.count(), 1)
        self.assertEqual(self.user_siae_2.siaes.count(), 0)  # setUpTestData

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demander le rattachement")

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.post(url)  # data={}
        self.assertEqual(response.status_code, 302)  # redirect to success_url
        self.assertEqual(response.url, "/profil/")
        self.assertEqual(self.siae_with_user.users.count(), 1)  # invitation workflow
        self.assertEqual(self.user_siae_2.siaes.count(), 0)


class DashboardSiaeEditViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.other_user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)
        cls.siae_without_user = SiaeFactory()

    def test_anonymous_user_cannot_edit_siae(self):
        url = reverse("dashboard:siae_search_by_siret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_siae_user_can_edit_siae(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard:siae_edit", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/profil/prestataires/{self.siae_with_user.slug}/modifier/recherche/")

        self.client.force_login(self.other_user_siae)
        url = reverse("dashboard:siae_edit", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # self.assertEqual(response.url, "/profil/")  # redirects first to siae_edit_search

    def test_only_siae_user_can_access_siae_edit_tabs(self):
        SIAE_EDIT_URLS = [
            "dashboard:siae_edit_search",
            "dashboard:siae_edit_info",
            "dashboard:siae_edit_offer",
            "dashboard:siae_edit_links",
            "dashboard:siae_edit_contact",
        ]
        self.client.force_login(self.user_siae)
        for siae_edit_url in SIAE_EDIT_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_user_siae)
        for siae_edit_url in SIAE_EDIT_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")


class DashboardSiaeUserViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_siae_2 = UserFactory(kind=User.KIND_SIAE)
        cls.other_user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_users = SiaeFactory()
        cls.siae_with_users.users.add(cls.user_siae)
        cls.siae_with_users.users.add(cls.user_siae_2)
        cls.siae_without_user = SiaeFactory()

    def test_only_siae_user_can_access_siae_users(self):
        SIAE_USER_URLS = [
            "dashboard:siae_users",
        ]
        self.client.force_login(self.user_siae)
        for siae_edit_url in SIAE_USER_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_users.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_user_siae)
        for siae_edit_url in SIAE_USER_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_users.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")

    def test_only_siae_user_can_delete_collaborator(self):
        self.assertEqual(self.siae_with_users.users.count(), 2)

        self.client.force_login(self.other_user_siae)
        siaeuser = SiaeUser.objects.get(siae=self.siae_with_users, user=self.user_siae)
        url = reverse("dashboard:siae_user_delete", args=[self.siae_with_users.slug, siaeuser.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

        self.client.force_login(self.user_siae)
        siaeuser = SiaeUser.objects.get(siae=self.siae_with_users, user=self.user_siae_2)
        url = reverse("dashboard:siae_user_delete", args=[self.siae_with_users.slug, siaeuser.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)  # 200? normal because redirects to dashboard:siae_users
        self.assertEqual(response.url, reverse("dashboard:siae_users", args=[self.siae_with_users.slug]))
        self.assertEqual(self.siae_with_users.users.count(), 1)
        # TODO: user should not be able to delete itself


class DashboardFavoriteListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_favorite_list = UserFactory(kind=User.KIND_BUYER)
        cls.other_user_favorite_list = UserFactory(kind=User.KIND_PARTNER)
        cls.favorite_list_1 = FavoriteListFactory(name="Liste 1", user=cls.user_favorite_list)
        cls.favorite_list_2 = FavoriteListFactory(name="Liste 2", user=cls.other_user_favorite_list)

    def test_anonymous_user_cannot_view_favorite_list(self):
        url = reverse("dashboard:profile_favorite_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

        url = reverse("dashboard:profile_favorite_list_detail", args=[self.favorite_list_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_favorite_list_user_can_access(self):
        self.client.force_login(self.user_favorite_list)
        url = reverse("dashboard:profile_favorite_list_detail", args=[self.favorite_list_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_user_favorite_list)
        url = reverse("dashboard:profile_favorite_list_detail", args=[self.favorite_list_1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")
