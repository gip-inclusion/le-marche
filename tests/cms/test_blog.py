from django.test import TestCase
from sites_conformes.blog.models import BlogEntryPage, BlogIndexPage
from sites_conformes.core.models import ContentPage
from wagtail.models import Site


class DisabledBlogTest(TestCase):
    def test_blog_pages_cannot_be_created(self):
        root_page = Site.objects.get(is_default_site=True).root_page

        self.assertFalse(BlogIndexPage.can_create_at(root_page))
        self.assertFalse(BlogEntryPage.can_create_at(root_page))
        self.assertNotIn(BlogIndexPage, root_page.specific_class.creatable_subpage_models())
        self.assertIn(ContentPage, root_page.specific_class.creatable_subpage_models())
