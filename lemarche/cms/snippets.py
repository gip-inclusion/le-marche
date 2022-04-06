from django.db import models
from wagtail.admin.edit_handlers import FieldPanel
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
