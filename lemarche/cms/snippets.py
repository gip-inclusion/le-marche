from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet


@register_snippet
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


@register_snippet
class Advert(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre de l'encart")
    image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    # call to action
    cta_url = models.URLField(null=True, blank=True)
    cta_id = models.SlugField(
        verbose_name="slug",
        allow_unicode=True,
        max_length=255,
        help_text="id du call to action (pour le suivi)",
    )
    cta_text = models.CharField(max_length=255, verbose_name="Titre du call to action")
    cta_open_in_new_tab = models.BooleanField(default=True, verbose_name="Ouvrir dans une nouvelle fenêtre")

    panels = [
        FieldPanel("title"),
        FieldPanel("image"),
        FieldPanel("cta_url"),
        FieldPanel("cta_id"),
        FieldPanel("cta_text"),
        FieldPanel("cta_open_in_new_tab"),
    ]

    class Meta:
        verbose_name = "Panneau publicitaire"
        verbose_name_plural = "Panneaux publicitaires"

    def __str__(self):
        return self.title


@register_snippet
class InfoCard(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre de l'encart")
    slug = models.SlugField(
        verbose_name="slug",
        allow_unicode=True,
        max_length=255,
        help_text="A slug to identify this info card",
    )

    content_card = models.TextField(verbose_name="Contenu")

    panels = [
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("content_card"),
    ]

    class Meta:
        verbose_name = "Carte info"
        verbose_name_plural = "Cartes infos"

    def __str__(self):
        return self.title


@register_snippet
class Paragraph(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre de l'encart")
    slug = models.SlugField(
        verbose_name="slug",
        unique=True,
        max_length=255,
        help_text="Identifiant",
    )

    content = RichTextField(
        blank=True,
        verbose_name="Contenu",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("content"),
    ]

    class Meta:
        verbose_name = "Paragraphe"
        verbose_name_plural = "Paragraphes"

    def __str__(self):
        return self.title
