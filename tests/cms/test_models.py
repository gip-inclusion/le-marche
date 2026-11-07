from django.test import RequestFactory, TestCase
from sites_conformes.core.models import ContentPage, Tag
from wagtail.models import PageViewRestriction, Site

from lemarche.cms.models import ArticleList


class ArticleListTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        root_page = Site.objects.get(is_default_site=True).root_page
        cls.article_list = root_page.add_child(instance=ArticleList(title="Articles", slug="articles-test"))
        cls.public_tag = Tag.objects.create(name="Public tag", slug="public-tag")
        cls.restricted_tag = Tag.objects.create(name="Restricted tag", slug="restricted-tag")

        cls.public_article = cls.article_list.add_child(instance=ContentPage(title="Public article"))
        cls.public_article.tags.add(cls.public_tag)
        cls.public_article.save()

        cls.restricted_article = cls.article_list.add_child(instance=ContentPage(title="Restricted article"))
        cls.restricted_article.tags.add(cls.restricted_tag)
        cls.restricted_article.save()
        PageViewRestriction.objects.create(
            page=cls.restricted_article, restriction_type=PageViewRestriction.PASSWORD, password="secret"
        )

    def test_get_posts_excludes_restricted_pages(self):
        self.assertQuerySetEqual(self.article_list.get_posts(), [self.public_article])

    def test_categories_exclude_tags_of_restricted_pages(self):
        self.article_list.posts = self.article_list.get_posts()
        context = self.article_list.get_context(RequestFactory().get("/"))
        self.assertQuerySetEqual(context["categories"], [self.public_tag])
