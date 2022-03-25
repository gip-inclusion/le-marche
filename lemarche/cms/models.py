from django import forms
from django.db import models
from django.db.models import Q
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


class ArticleCategory(models.Model):
    """Article catgory for a snippet."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(
        verbose_name="slug",
        allow_unicode=True,
        max_length=255,
        help_text="A slug to identify posts by this category",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
    ]

    class Meta:
        verbose_name = "Catégorie d'articles"
        verbose_name_plural = "Catégories d'articles"
        ordering = ["name"]

    def __str__(self):
        return self.name


register_snippet(ArticleCategory)


class ArticlePage(Page):
    intro = models.TextField(verbose_name="Introduction", null=True, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    categories = ParentalManyToManyField("cms.ArticleCategory", blank=True)

    is_static_page = models.BooleanField(verbose_name="c'est une page statique ?", default=False)

    template_name = models.CharField(
        verbose_name="nom de la template",
        help_text="Nom du fichier présent dans 'templates/cms/static', ex: valoriser-achats.html",
        max_length=90,
        blank=True,
    )
    # Database fields
    body = RichTextField(blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_static_page:
            self.template = f"cms/static/{self.template_name}"

    # Search index configuration

    search_fields = Page.search_fields + [
        index.FilterField("intro"),
        index.SearchField("body"),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        MultiFieldPanel([FieldPanel("categories", widget=forms.CheckboxSelectMultiple)], heading="Categories"),
        ImageChooserPanel("image"),
        MultiFieldPanel(
            [
                FieldPanel("is_static_page", classname="full"),
                FieldPanel("template_name", classname="full"),
            ],
            heading="Article statique",
        ),
        MultiFieldPanel(
            [
                FieldPanel("body", classname="full"),
            ],
            heading="Article normal",
        ),
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
        context["categories"] = ArticleCategory.objects.all()
        return context

    def get_posts(self):
        return ArticlePage.objects.descendant_of(self).live().order_by("-last_published_at")

    @route(r"^$")
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_posts()
        return self.render(
            request,
        )

    @route(r"^categorie/(?P<cat_slug>[-\w]*)/$", name="category_view")
    def category_view(self, request, cat_slug, *args, **kwargs):
        """Find blog posts based on a category."""
        self.posts = self.get_posts()
        context = self.get_context(request)

        try:
            # Look for the blog category by its slug.
            category = ArticleCategory.objects.get(slug=cat_slug)
        except Exception:
            # Blog category doesnt exist (ie /blog/category/missing-category/)
            # Redirect to self.url, return a 404.. that's up to you!
            category = None
        if category is not None:
            context["article_list"] = self.posts.filter(categories__in=[category])
            context["category"] = category
        return self.render(
            request,
            context_overrides=context,
        )

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
        return self.render(
            request,
        )

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["cms.ArticlePage"]
