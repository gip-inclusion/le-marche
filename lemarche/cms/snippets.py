from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet


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
