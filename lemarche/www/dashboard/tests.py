from django.test import TestCase
from django.urls import reverse

from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.users.models import User


class DashboardHomeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_with_api_token = UserFactory(api_key="admin")

    def test_anonymous_user_cannot_access_profile(self):
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/profil/")

    def user_can_access_profile(self):
        self.client.login(email=self.user.email, password=DEFAULT_PASSWORD)
        url = reverse("dashboard:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def user_buyer_should_not_have_siae_section(self):
        self.client.login(email=self.user_buyer.email, password=DEFAULT_PASSWORD)
        url = reverse("dashboard:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mes structures")

    def user_with_api_key_should_have_api_section(self):
        self.client.login(email=self.user_with_api_token.email, password=DEFAULT_PASSWORD)
        url = reverse("dashboard:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Accès API")


class SiaeSearchAdoptViewTest(TestCase):
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
            self.client.login(email=user.email, password=DEFAULT_PASSWORD)
            url = reverse("dashboard:siae_search_by_siret")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        NOT_ALLOWED_USERS = [self.user_buyer, self.user_partner]
        for user in NOT_ALLOWED_USERS:
            self.client.login(email=user.email, password=DEFAULT_PASSWORD)
            url = reverse("dashboard:siae_search_by_siret")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")

    def test_only_siaes_without_users_can_be_adopted(self):
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_only_new_siae_user_can_adopt_confirm(self):
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        self.assertEqual(self.siae_with_user.users.count(), 1)
        self.assertEqual(self.user_siae.siaes.count(), 1)  # setUpTestData

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_siae_without_user_adopt_confirm(self):
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        self.assertEqual(self.siae_without_user.users.count(), 0)
        self.assertEqual(self.user_siae.siaes.count(), 1)  # setUpTestData

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Je confirme")

        url = reverse("dashboard:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.post(url)  # data={}
        self.assertEqual(response.status_code, 302)  # redirect to success_url
        self.assertEqual(response.url, "/profil/")
        self.assertEqual(self.siae_without_user.users.count(), 1)
        self.assertEqual(self.user_siae.siaes.count(), 1 + 1)

    def test_siae_with_existing_user_adopt_confirm(self):
        self.client.login(email=self.user_siae_2.email, password=DEFAULT_PASSWORD)
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


class SiaeEditView(TestCase):
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
        # self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_siae_user_can_edit_siae(self):
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        url = reverse("dashboard:siae_edit", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/profil/prestataires/{self.siae_with_user.slug}/modifier/info-contact/")

        self.client.login(email=self.other_user_siae.email, password=DEFAULT_PASSWORD)
        url = reverse("dashboard:siae_edit", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # self.assertEqual(response.url, "/profil/")  # redirects first to siae_users

    def test_only_siae_user_can_access_siae_edit_tabs(self):
        SIAE_EDIT_URLS = [
            "dashboard:siae_edit_info_contact",
            "dashboard:siae_edit_offer",
            "dashboard:siae_edit_presta",
            "dashboard:siae_edit_other",
            "dashboard:siae_users",
        ]
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        for siae_edit_url in SIAE_EDIT_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        self.client.login(email=self.other_user_siae.email, password=DEFAULT_PASSWORD)
        for siae_edit_url in SIAE_EDIT_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")

    def test_only_siae_user_can_access_siae_users(self):
        SIAE_USER_URLS = [
            "dashboard:siae_users",
        ]
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        for siae_edit_url in SIAE_USER_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        self.client.login(email=self.other_user_siae.email, password=DEFAULT_PASSWORD)
        for siae_edit_url in SIAE_USER_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")
