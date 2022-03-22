from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
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

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = []


class ArticlePageRelatedLink(Orderable):
    page = ParentalKey(ArticlePage, on_delete=models.CASCADE, related_name="related_links")
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel("name"),
        FieldPanel("url"),
    ]
