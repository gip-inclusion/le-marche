from django.db import models
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.fields import StreamField
from wagtail.models import Page

from content_manager.models import ContentPage, Tag
from lemarche.cms import blocks


class ArticleList(RoutablePageMixin, Page):
    def get_context(self, request, *args, **kwargs):
        context = super(ArticleList, self).get_context(request, *args, **kwargs)
        context["article_list"] = self.posts
        context["search_type"] = getattr(self, "search_type", "")
        context["search_term"] = getattr(self, "search_term", "")
        context["categories"] = (
            Tag.objects.filter(contentpage__in=ContentPage.objects.descendant_of(self).live())
            .annotate(usecount=Count("contentpage"))
            .filter(usecount__gte=1)
            .order_by("name")
        )

        return context

    def get_posts(self):
        return ContentPage.objects.descendant_of(self).live().prefetch_related("tags").order_by("-last_published_at")

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

        tag = get_object_or_404(Tag, slug=cat_slug)
        context["article_list"] = self.posts.filter(tags__in=[tag])
        context["category"] = tag
        return self.render(request, context_overrides=context)

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

    subpage_types = ["content_manager.ContentPage"]


class HomePage(Page):
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
    banner_cta_section = StreamField(
        [
            ("cta_primary", blocks.CallToAction(label="CTA primaire")),
            ("cta_secondary", blocks.CallToAction(label="CTA secondaire")),
            ("cta_primary_auth", blocks.CallToAction(label="CTA primaire connecté")),
            ("cta_secondary_auth", blocks.CallToAction(label="CTA secondaire connecté")),
        ],
        min_num=1,
        max_num=4,
        use_json_field=True,
        null=True,
    )

    content = StreamField(
        [
            ("website_stats", blocks.StatsWebsite()),
            ("section_they_publish_tenders", blocks.TendersTestimonialsSection()),
            ("section_studies_cases_tenders", blocks.TendersStudiesCasesSection()),
            ("section_our_siaes", blocks.OurSiaesSection()),  # TODO: to be remove after deploy
            ("section_ecosystem", blocks.EcosystemSection()),
            ("section_our_ressources", blocks.OurRessourcesSection()),
            ("section_what_find_here", blocks.WhatFindHereSection()),
            ("section_our_partners", blocks.OurPartnersSection()),
            ("section_our_features", blocks.OurFeaturesSection()),
            ("section_why_call_siaes", blocks.WhyCallSiaes()),
        ],
        null=True,
        block_counts={
            "website_stats": {"max_num": 1},
            "section_they_publish_tenders": {"max_num": 1},
            "section_studies_cases_tenders": {"max_num": 1},
            "section_our_siaes": {"max_num": 1},
            "section_our_ressources": {"max_num": 1},
            "section_what_find_here": {"max_num": 1},
            "section_our_partners": {"max_num": 1},
            "section_our_features": {"max_num": 1},
            "section_why_call_siaes": {"max_num": 1},
        },
        use_json_field=True,
    )

    sub_header_custom_message = StreamField(
        [
            ("message", RichTextBlock(label="Message personnalisé du bandeau")),
        ],
        blank=True,
        null=True,
        verbose_name="Message personnalisé du bandeau",
        help_text="Contenu affiché dans le bandeau sous l'en-tête.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("sub_header_custom_message"),
        FieldPanel("banner_title"),
        FieldPanel("banner_subtitle"),
        FieldPanel("banner_arguments_list"),
        FieldPanel("banner_cta_section"),
        FieldPanel("content"),
    ]

    page_description = "Use this page type like a landing page"
    parent_page_types = ["wagtailcore.Page", "cms.HomePage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["sub_header_custom_message"] = self.sub_header_custom_message
        return context


class FAQPage(Page):
    intro = models.TextField(verbose_name="Introduction de la page", null=True, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        FieldPanel(
            "image",
            classname="collapsible",
        ),
        FieldPanel("faqs"),
    ]

    faqs = StreamField(
        [
            ("faq_group", blocks.FAQGroupBlock()),
        ],
        blank=True,
        use_json_field=True,
    )

    parent_page_types = ["wagtailcore.Page", "cms.HomePage", "cms.ArticleList"]

    class Meta:
        verbose_name = "FAQ Page"
        verbose_name_plural = "FAQ Pages"
