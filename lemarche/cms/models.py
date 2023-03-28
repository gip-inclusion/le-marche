from django import forms
from django.conf import settings
from django.db import models
from django.db.models import Q
from modelcluster.fields import ParentalManyToManyField
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from lemarche.cms import blocks
from lemarche.cms.forms import ArticlePageForm
from lemarche.cms.snippets import ArticleCategory


class ArticlePage(Page):
    intro = models.TextField(verbose_name="Introduction", null=True, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    categories = ParentalManyToManyField("cms.ArticleCategory", blank=True)

    is_static_page = models.BooleanField(verbose_name="c'est une page statique ?", default=False)
    with_cta_tender = models.BooleanField(verbose_name="avec un CTA pour les besoins ?", default=False)

    template_name = models.CharField(
        verbose_name="Nom de la template",
        help_text="Nom du fichier présent dans 'templates/cms/static', ex: valoriser-achats.html",
        max_length=90,
        blank=True,
    )
    # Database fields
    body = RichTextField(
        blank=True, verbose_name="Contenu de l'article", features=settings.WAGTAIL_RICHTEXT_FIELD_FEATURES
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_static_page:
            self.template = f"cms/static/{self.template_name}"

    base_form_class = ArticlePageForm

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        FieldPanel("with_cta_tender", classname="full"),
        MultiFieldPanel([FieldPanel("categories", widget=forms.CheckboxSelectMultiple)], heading="Categories"),
        FieldPanel(
            "image",
            classname="collapsible",
        ),
        MultiFieldPanel(
            [
                FieldPanel("body", classname="full"),
            ],
            heading="Article normal",
            classname="collapsible",
        ),
        MultiFieldPanel(
            [
                FieldPanel("with_cta_tender", classname="full"),
            ],
            heading="Promotion",
            classname="collapsible",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_static_page", classname="full"),
                FieldPanel("template_name", classname="full"),
            ],
            heading="Article statique",
            classname="collapsible collapsed",
        ),
    ]

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
        return (
            ArticlePage.objects.prefetch_related("categories")
            .descendant_of(self)
            .live()
            .order_by("-last_published_at")
        )

    @route(r"^$")
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_posts()
        return self.render(
            request,
        )

    @route(r"^categories/(?P<cat_slug>[-\w]*)/$", name="category_view")
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

    # parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.ArticlePage"]


class HomePage(Page):
    max_count = 1
    banner_title = models.CharField(
        default="Votre recherche de prestataires inclusifs est chronophage ?", max_length=120
    )
    banner_subtitle = models.CharField(
        blank=True, max_length=120, default="Confiez votre sourcing au marché de l'inclusion !"
    )
    banner_arguments_list = StreamField(
        [
            ("item", wagtail_blocks.CharBlock()),
        ],
        min_num=3,
        max_num=3,
        use_json_field=True,
    )
    # banner_image = models.ForeignKey(
    #     "wagtailimages.Image",
    #     null=True,
    #     blank=False,
    #     on_delete=models.SET_NULL,
    #     # related_name=''
    # )
    banner_cta_id = models.SlugField(
        default="home-demande",
        verbose_name="slug",
        allow_unicode=True,
        max_length=255,
        help_text="id du call to action (pour le suivi)",
    )
    banner_cta_text = models.CharField(
        default="Publier un besoin d'achat", max_length=255, verbose_name="Titre du call to action"
    )

    content = StreamField(
        [
            ("website_stats", blocks.StatsWebsite()),
            ("section_they_publish_tenders", blocks.TendersTestimonialsSection()),
            ("section_studies_cases_tenders", blocks.TendersStudiesCasesSection()),
            ("section_our_siaes", blocks.OurSiaesSection()),
            ("section_our_ressources", blocks.OurRessourcesSection()),
            ("section_what_find_here", blocks.WhatFindHereSection()),
            ("section_our_partners", blocks.OurPartnersSection()),
        ],
        null=True,
        block_counts={
            "website_stats": {"min_num": 1, "max_num": 1},
            "section_they_publish_tenders": {"min_num": 1, "max_num": 1},
            "section_studies_cases_tenders": {"min_num": 1, "max_num": 1},
            "section_our_siaes": {"min_num": 1, "max_num": 1},
            "section_our_ressource": {"min_num": 1, "max_num": 1},
            "section_what_find_her": {"min_num": 1, "max_num": 1},
            "section_our_partners": {"min_num": 1, "max_num": 1},
        },
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("banner_title"),
        FieldPanel("banner_subtitle"),
        FieldPanel("banner_cta_id"),
        FieldPanel("banner_cta_text"),
        FieldPanel("banner_arguments_list"),
        FieldPanel("content"),
    ]

    parent_page_types = ["wagtailcore.Page"]
