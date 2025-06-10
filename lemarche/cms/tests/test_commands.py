import json
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase
from wagtail.models import Page, Site

from content_manager.models import ContentPage


class CreateContentPagesCommandTest(TestCase):
    def setUp(self):
        self.root_page = Page.get_root_nodes().first()
        self.home_page = Page(title="Accueil")
        self.root_page.add_child(instance=self.home_page)
        self.home_page.save_revision().publish()

        # We change root_page of default site
        Site.objects.filter(hostname="localhost", is_default_site=True).update(root_page=self.home_page)

    def test_parent_page_setup(self):
        """Test the parent page for the home page is correctly set up"""
        self.assertIsNotNone(self.root_page, "La page racine n'a pas été trouvée.")
        self.assertIsNotNone(self.home_page, "La page parente 'Accueil' n'a pas été trouvée.")
        self.assertTrue(self.home_page.live, "La page parente 'Accueil' n'est pas publiée.")
        self.assertIn(
            self.home_page, self.root_page.get_children(), "La page 'Accueil' n'est pas un enfant direct de la racine."
        )

        response = self.client.get(self.home_page.get_url())
        self.assertEqual(
            response.status_code,
            200,
            f"La page d'accueil n'est pas accessible (status: {response.status_code}).",
        )

    def test_create_content_pages_with_json(self):
        """Test the content pages are correctly created from the JSON file"""
        with open("lemarche/fixtures/cms_content_pages.json") as f:
            pages_data = json.load(f)

        call_command("create_content_pages", stdout=StringIO())

        for page_data in pages_data:
            slug = page_data["slug"]

            try:
                page = ContentPage.objects.get(slug=slug)
            except ContentPage.DoesNotExist:
                self.fail(f"La page avec le slug '{slug}' n'a pas été trouvée.")

            self.assertEqual(
                page.get_parent(), self.home_page, f"La page '{slug}' n'est pas reliée à la page 'Accueil'."
            )

            client = Client()
            response = client.get(page.get_url())
            self.assertEqual(
                response.status_code,
                200,
                f"La page avec le slug '{slug}' n'est pas accessible (status: {response.status_code}).",
            )

    def test_prevent_duplicate_page_creation(self):
        """Test the command does not create duplicate pages"""
        self.home_page.add_child(instance=ContentPage(slug="mentions-legales", title="Mentions légales"))

        call_command("create_content_pages", stdout=StringIO())

        self.assertEqual(
            ContentPage.objects.filter(slug="mentions-legales").count(),
            1,
            msg="Une page en double a été créée pour le slug 'mentions-legales'.",
        )
