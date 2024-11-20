import json

from django.core.management import call_command
from django.test import Client, TestCase
from wagtail.models import Site

from content_manager.models import ContentPage


class CreateContentPagesCommandTests(TestCase):
    def test_create_content_pages_with_json(self):
        client = Client()
        with open("lemarche/fixtures/cms_content_pages.json") as f:
            pages_data = json.load(f)

        call_command("create_content_pages")

        # Check that the pages were created
        for page_data in pages_data:
            slug = page_data["slug"]
            self.assertTrue(
                ContentPage.objects.filter(slug=slug).exists(), msg=f"La page avec le slug '{slug}' n'a pas été créée."
            )

            response = client.get(f"/{slug}/")
            self.assertEqual(
                response.status_code,
                200,
                msg=f"La page avec le slug '{slug}' n'est pas accessible (status: {response.status_code}).",
            )

    def test_prevent_duplicate_page_creation(self):
        """Ensure the command does not create duplicate pages"""
        home_page = Site.objects.get(is_default_site=True).root_page
        home_page.add_child(instance=ContentPage(slug="mentions-legales", title="Mentions légales"))

        call_command("create_content_pages")

        self.assertEqual(
            ContentPage.objects.filter(slug="mentions-legales").count(),
            1,
            msg="Une page en double a été créée pour le slug 'mentions-legales'.",
        )
