from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory
from lemarche.users.models import User

from wagtail.models import Page as WagtailPage
from wagtail.models import Site

import xml.etree.ElementTree as ET


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

        # top header banner
        self.assertContains(response, "Vous êtes une structure inclusive")
        self.assertContains(response, "header-for-siaes-link")
        self.assertNotContains(response, "Vous êtes acheteur")
        self.assertNotContains(response, "header-for-buyers-link")

        self.assertContains(response, "Publier un besoin d'achat")
        self.assertContains(response, reverse("tenders:create"))

        self.assertContains(response, "S'inscrire")
        self.assertNotContains(response, "Référencer ma structure")
        self.assertContains(response, reverse("auth:signup"))

        self.assertContains(response, "Se connecter")
        self.assertContains(response, reverse("auth:login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertNotContains(response, "Tableau de bord")
        self.assertNotContains(response, reverse("dashboard:home"))

        self.assertNotContains(response, "Déconnexion")
        self.assertNotContains(response, reverse("auth:logout"))

    def test_anonymous_user_home_for_siae(self):
        response = self.client.get("/accueil-structure/")

        # top header banner
        self.assertNotContains(response, "Vous êtes une structure inclusive")
        self.assertNotContains(response, "header-for-siaes-link")
        self.assertContains(response, "Vous êtes acheteur")
        self.assertContains(response, "header-for-buyers-link")

        self.assertContains(response, "Publier un besoin d")
        self.assertContains(response, reverse("tenders:create"))

        self.assertNotContains(response, "S'inscrire")
        self.assertContains(response, "Référencer ma structure")
        self.assertContains(response, reverse("auth:signup"))

        self.assertContains(response, "Se connecter")
        self.assertContains(response, reverse("auth:login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertNotContains(response, "Tableau de bord")
        self.assertNotContains(response, reverse("dashboard:home"))

        self.assertNotContains(response, "Déconnexion")
        self.assertNotContains(response, reverse("auth:logout"))

    def test_siae_user_home(self):
        self.client.force_login(self.siae_user)
        response = self.client.get("/")

        # top header banner
        self.assertNotContains(response, "Vous êtes une structure inclusive")
        self.assertNotContains(response, "header-for-siaes-link")
        self.assertNotContains(response, "Vous êtes acheteur")
        self.assertNotContains(response, "header-for-buyers-link")

        self.assertContains(response, "Publier un besoin d'achat")
        self.assertContains(response, reverse("tenders:create"))

        self.assertNotContains(response, "S'inscrire")
        self.assertNotContains(response, "Référencer ma structure")
        self.assertNotContains(response, reverse("auth:signup"))

        self.assertNotContains(response, "Se connecter")
        self.assertNotContains(response, reverse("auth:login"))

        self.assertContains(response, "Demandes reçues")
        self.assertContains(response, f'"{reverse("tenders:list")}"')

        self.assertContains(response, "Tableau de bord")
        self.assertContains(response, reverse("dashboard:home"))

        self.assertContains(response, "Déconnexion")
        self.assertContains(response, reverse("auth:logout"))

    def test_buyer_user_home(self):
        self.client.force_login(self.user_buyer)
        response = self.client.get("/")

        # top header banner
        self.assertNotContains(response, "Vous êtes une structure inclusive")
        self.assertNotContains(response, "header-for-siaes-link")
        self.assertNotContains(response, "Vous êtes acheteur")
        self.assertNotContains(response, "header-for-buyers-link")

        self.assertContains(response, "Publier un besoin d'achat")
        self.assertContains(response, reverse("tenders:create"))

        self.assertNotContains(response, "S'inscrire")
        self.assertNotContains(response, "Référencer ma structure")
        self.assertNotContains(response, reverse("auth:signup"))

        self.assertNotContains(response, "Se connecter")
        self.assertNotContains(response, reverse("auth:login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertContains(response, "Tableau de bord")
        self.assertContains(response, reverse("dashboard:home"))

        self.assertContains(response, "Déconnexion")
        self.assertContains(response, reverse("auth:logout"))


class SitemapTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # WagtailPage creation for tests
        root = WagtailPage.get_first_root_node()
        Site.objects.create(
            hostname="testserver",
            root_page=root,
            is_default_site=True,
            site_name="testserver",
        )
        cls.tests_page_list = root.add_child(
            instance=WagtailPage(
                title="Tests Page List",
                slug="tests-page-list",
                depth=2,
                last_published_at=timezone.now(),
            )
        )

        cls.test_page_1 = cls.tests_page_list.add_child(
            instance=WagtailPage(
                title="Test Page 1",
                slug="test-page-1",
                depth=3,
                last_published_at=timezone.now(),
            )
        )

    def test_sitemap_xml_exists(self):
        """Test the sitemap xml exists"""
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)

    def test_sitemap_xml_is_not_empty(self):
        """Test the sitemap xml is not empty and contains urls"""
        response = self.client.get(reverse("sitemap"))

        self.assertGreater(len(response.content), 0)

    def test_sitemap_xml_is_valid(self):
        """Test the sitemap xml is valid"""
        response = self.client.get(reverse("sitemap"))

        try:
            ET.fromstring(response.content)
        except ET.ParseError:
            self.fail("Le sitemap n'est pas dans un format XML valide.")

    def test_sitemap_xml_contains_urls(self):
        """Test the sitemap xml contains URLs"""
        response = self.client.get(reverse("sitemap"))
        test_page_url = self.test_page_1.full_url

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"<loc>{test_page_url}</loc>")

    def test_urls_contain_lastmod_tag(self):
        """Test the sitemap xml contains the lastmod tag for URLs."""
        response = self.client.get(reverse("sitemap"))
        lastmod = self.test_page_1.last_published_at.strftime("%Y-%m-%d")

        self.assertContains(response, f"<lastmod>{lastmod}</lastmod>")

    def test_sitemap_html_exists(self):
        """Test the sitemap html exists"""
        response = self.client.get("/plan-du-site/")

        self.assertEqual(response.status_code, 200)

    def test_sitemap_html_is_not_empty(self):
        """Test 'plan_du_site.html' is not empty and contains urls"""
        response = self.client.get("/plan-du-site/")

        self.assertGreater(len(response.content), 0)
        self.assertContains(response, "Plan du site")

    def test_sitemap_html_returns_all_urls(self):
        """Test 'plan_du_site.html' contains all urls"""
        response = self.client.get("/plan-du-site/")

        content = response.content.decode()
        self.assertIn("/tests-page-list/", content)
        self.assertIn("/tests-page-list/test-page-1/", content)
