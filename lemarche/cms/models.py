from django.db import models
from django.db.models import Q
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.fields import RichTextField
from wagtail.core.models import Orderable, Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index


class ArticlePage(Page):

    # Database fields
    intro = models.TextField()
    body = RichTextField()
    image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    # Search index configuration

    search_fields = Page.search_fields + [
        index.FilterField("intro"),
        index.SearchField("body"),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        FieldPanel("body", classname="full"),
        InlinePanel("related_links", label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel("image"),
    ]

    # Parent page / subpage type rules

    parent_page_types = ["cms.ArticleList"]
    subpage_types = []


class ArticlePageRelatedLink(Orderable):
    page = ParentalKey(ArticlePage, on_delete=models.CASCADE, related_name="related_links")
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel("name"),
        FieldPanel("url"),
    ]


class ArticleList(RoutablePageMixin, Page):
    def get_context(self, request, *args, **kwargs):
        context = super(ArticleList, self).get_context(request, *args, **kwargs)
        context["article_list"] = self.posts
        context["search_type"] = getattr(self, "search_type", "")
        context["search_term"] = getattr(self, "search_term", "")
        return context

    def get_posts(self):
        return ArticlePage.objects.descendant_of(self).live().order_by("-last_published_at")

    @route(r"^$")
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_posts()
        return Page.serve(self, request, *args, **kwargs)

    @route(r"^search/$")
    def post_search(self, request, *args, **kwargs):
        search_query = request.GET.get("q", None)
        self.posts = self.get_posts()
        if search_query:
            self.posts = self.posts.filter(
                Q(body__icontains=search_query) | Q(title__icontains=search_query) | Q(excerpt__icontains=search_query)
            )

        self.search_term = search_query
        self.search_type = "search"
        return Page.serve(self, request, *args, **kwargs)

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["cms.ArticlePage"]
