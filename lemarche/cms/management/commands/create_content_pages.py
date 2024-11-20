import json

from django.core.management.base import BaseCommand
from wagtail.models import Site

from content_manager.models import ContentPage


class Command(BaseCommand):
    help = """
    Creates a series of content pages.
    """

    def handle(self, *args, **kwargs):
        try:
            with open("lemarche/fixtures/cms_content_pages.json") as f:
                pages_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR("Le fichier content_manager/fixtures/cms_content_pages.json n'existe pas.")
            )
            return
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(
                    "Le fichier content_manager/fixtures/cms_content_pages.json n'est pas un fichier JSON valide."
                )
            )
            return

        home_page = Site.objects.filter(is_default_site=True).first().root_page

        for page_data in pages_data:
            slug = page_data["slug"]
            title = page_data["title"]
            body = page_data.get("body", [])

            self.create_content_page(slug, title, body, home_page)

    def create_content_page(self, slug: str, title: str, body: list, parent_page: ContentPage) -> ContentPage:
        """
        Creates a page for the site.
        """

        # Don't replace or duplicate an already existing page
        already_exists = ContentPage.objects.filter(slug=slug).first()
        if already_exists:
            self.stdout.write(f"The {slug} page seem to already exist with id {already_exists.id}")
            return already_exists

        new_page = parent_page.add_child(instance=ContentPage(title=title, body=body, slug=slug, show_in_menus=True))

        self.stdout.write(self.style.SUCCESS(f"Page {slug} created with id {new_page.id}"))

        return new_page
