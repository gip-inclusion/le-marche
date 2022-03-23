from django.db import models
from django.db.models import Q
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index


class BaseArticle(Page):
    intro = models.TextField(verbose_name="Introduction", null=True, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        abstract = True

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
    ]

    promote_panels = [
        ImageChooserPanel("image"),
        MultiFieldPanel(Page.promote_panels, "Configuration SEO"),
    ]


class ArticlePage(BaseArticle):

    # Database fields
    body = RichTextField()

    # Search index configuration

    search_fields = BaseArticle.search_fields + [
        index.FilterField("intro"),
        index.SearchField("body"),
    ]

    # Editor panels configuration

    content_panels = BaseArticle.content_panels + [
        FieldPanel("body", classname="full"),
    ]

    # Parent page / subpage type rules

    parent_page_types = ["cms.ArticleList"]
    subpage_types = []


class ArticleList(RoutablePageMixin, Page):
    def get_context(self, request, *args, **kwargs):
        context = super(ArticleList, self).get_context(request, *args, **kwargs)
        context["article_list"] = self.posts
        context["search_type"] = getattr(self, "search_type", "")
        context["search_term"] = getattr(self, "search_term", "")
        return context

    def get_posts(self):
        return self.get_children().live().order_by("-last_published_at")

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
    subpage_types = ["cms.ArticlePage", "cms.StaticPage"]


class StaticPage(BaseArticle):
    template_name = models.CharField(
        verbose_name="nom de la template",
        help_text="Nom du fichier présent dans 'templates/cms/static', ex: valoriser-achats.html",
        max_length=90,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = f"cms/static/{self.template_name}"

    content_panels = BaseArticle.content_panels + [
        FieldPanel("template_name", classname="full"),
    ]
