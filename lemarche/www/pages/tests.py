from django.test import TestCase
from django.urls import reverse

from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class PagesHeaderLinkTest(TestCase):
    fixtures = [
        "lemarche/fixtures/django/0a_networks.json",
        "lemarche/fixtures/django/0e_companies.json",
        "lemarche/fixtures/django/02_users.json",
        "lemarche/fixtures/django/20_cms.json",
    ]

    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.siae_user = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae])
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER, company_name="Entreprise Buyer")

    def test_anonymous_user_home(self):
        response = self.client.get("/")

        self.assertContains(response, "Vous êtes une structure inclusive")
        self.assertContains(response, "/accueil-structure/")

        self.assertContains(response, "Publier un besoin d'achat")
        self.assertContains(response, reverse("tenders:create"))

        self.assertContains(response, "S'inscrire")
        self.assertNotContains(response, "Référencer ma structure")
        self.assertContains(response, reverse("auth:signup"))

        self.assertContains(response, "Se connecter")
        self.assertContains(response, reverse("auth:login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertNotContains(response, "Mon espace")
        self.assertNotContains(response, reverse("dashboard:home"))

    def test_anonymous_user_home_for_siae(self):
        response = self.client.get("/accueil-structure/")

        self.assertNotContains(response, "Vous êtes une structure inclusive")
        self.assertNotContains(response, "/accueil-structure/")

        self.assertContains(response, "Publier un besoin d")
        self.assertContains(response, reverse("tenders:create"))

        self.assertNotContains(response, "S'inscrire")
        self.assertContains(response, "Référencer ma structure")
        self.assertContains(response, reverse("auth:signup"))

        self.assertContains(response, "Se connecter")
        self.assertContains(response, reverse("auth:login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertNotContains(response, "Mon espace")
        self.assertNotContains(response, reverse("dashboard:home"))

    def test_siae_user_home(self):
        self.client.force_login(self.siae_user)
        response = self.client.get("/")

        self.assertNotContains(response, "Vous êtes une structure inclusive")
        self.assertNotContains(response, "/accueil-structure/")

        self.assertContains(response, "Publier un besoin d'achat")
        self.assertContains(response, reverse("tenders:create"))

        self.assertNotContains(response, "S'inscrire")
        self.assertNotContains(response, "Référencer ma structure")
        self.assertNotContains(response, reverse("auth:signup"))

        self.assertNotContains(response, "Se connecter")
        self.assertNotContains(response, reverse("auth:login"))

        self.assertContains(response, "Demandes reçues")
        self.assertContains(response, f'"{reverse("tenders:list")}"')

        self.assertContains(response, "Mon espace")
        self.assertContains(response, reverse("dashboard:home"))

    def test_buyer_user_home(self):
        self.client.force_login(self.user_buyer)
        response = self.client.get("/")

        self.assertNotContains(response, "Vous êtes une structure inclusive")
        self.assertNotContains(response, "/accueil-structure/")

        self.assertContains(response, "Publier un besoin d'achat")
        self.assertContains(response, reverse("tenders:create"))

        self.assertNotContains(response, "S'inscrire")
        self.assertNotContains(response, "Référencer ma structure")
        self.assertNotContains(response, reverse("auth:signup"))

        self.assertNotContains(response, "Se connecter")
        self.assertNotContains(response, reverse("auth:login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertContains(response, "Mon espace")
        self.assertContains(response, reverse("dashboard:home"))
