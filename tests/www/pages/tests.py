import xml.etree.ElementTree as ET

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from wagtail.models import Page as WagtailPage, Site

from lemarche.users.models import User
from tests.siaes.factories import SiaeFactory
from tests.users.factories import UserFactory


class PagesHeaderLinkTest(TestCase):
    fixtures = [
        "lemarche/fixtures/django/0a_networks.json",
        "lemarche/fixtures/django/0d_labels.json",
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
        self.assertContains(response, reverse("account_signup"))

        self.assertContains(response, "Se connecter")
        self.assertContains(response, reverse("account_login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertNotContains(response, "Tableau de bord")
        self.assertNotContains(response, reverse("dashboard:home"))

        self.assertNotContains(response, "Déconnexion")
        self.assertNotContains(response, reverse("account_logout"))

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
        self.assertContains(response, reverse("account_signup"))

        self.assertContains(response, "Se connecter")
        self.assertContains(response, reverse("account_login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertNotContains(response, "Tableau de bord")
        self.assertNotContains(response, reverse("dashboard:home"))

        self.assertNotContains(response, "Déconnexion")
        self.assertNotContains(response, reverse("account_logout"))

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
        self.assertNotContains(response, reverse("account_signup"))

        self.assertNotContains(response, "Se connecter")
        self.assertNotContains(response, reverse("account_login"))

        self.assertContains(response, "Demandes reçues")
        self.assertContains(response, f'"{reverse("tenders:list")}"')

        self.assertContains(response, "Tableau de bord")
        self.assertContains(response, reverse("dashboard:home"))

        self.assertContains(response, "Déconnexion")
        self.assertContains(response, reverse("account_logout"))

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
        self.assertNotContains(response, reverse("account_signup"))

        self.assertNotContains(response, "Se connecter")
        self.assertNotContains(response, reverse("account_login"))

        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, f'"{reverse("tenders:list")}"')

        self.assertContains(response, "Tableau de bord")
        self.assertContains(response, reverse("dashboard:home"))

        self.assertContains(response, "Déconnexion")
        self.assertContains(response, reverse("account_logout"))


class SitemapTests(TestCase):
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
        cls.wagtail_page = root.add_child(
            instance=WagtailPage(
                title="Test WagtailPage",
                slug="test-wagtail-page",
                depth=2,
                path="0002",
                last_published_at=timezone.now(),
            )
        )

    def test_sitemap_xml(self):
        """Test sitemap.xml exists"""
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)

    def test_sitemap_xml_is_not_empty(self):
        """Test sitemap is not empty and contains urls"""
        response = self.client.get(reverse("sitemap"))

        self.assertGreater(len(response.content), 0)

    def test_sitemap_is_valid_xml(self):
        """Test sitemap is valid XML"""
        response = self.client.get(reverse("sitemap"))

        try:
            ET.fromstring(response.content)
        except ET.ParseError:
            self.fail("Le sitemap n'est pas dans un format XML valide.")

    def test_sitemap_xml_contains_wagtail_page(self):
        """Test the sitemap contains the wagtail page URL."""
        response = self.client.get(reverse("sitemap"))
        wagtail_page_url = self.wagtail_page.full_url

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"<loc>{wagtail_page_url}</loc>")

    def test_wagtail_page_contains_lastmod_tag(self):
        """Test the sitemap contains the lastmod tag for the wagtail page."""
        response = self.client.get(reverse("sitemap"))
        lastmod = self.wagtail_page.last_published_at.strftime("%Y-%m-%d")

        self.assertContains(response, f"<lastmod>{lastmod}</lastmod>")

    def test_sitemap_html(self):
        """Test that the HTML sitemap page is accessible"""
        response = self.client.get("/plan-du-site/")
        self.assertEqual(response.status_code, 200)

    def test_sitemap_html_contains_wagtail_page(self):
        """Test that the HTML sitemap contains the wagtail page URL and title"""
        response = self.client.get("/plan-du-site/")
        wagtail_page_url = self.wagtail_page.get_full_url()
        wagtail_page_title = self.wagtail_page.title

        self.assertContains(response, f'href="{wagtail_page_url}"')
        self.assertContains(response, wagtail_page_title)
