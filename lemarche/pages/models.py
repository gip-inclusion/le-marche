from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.utils import timezone


class Page(FlatPage):
    """
    A static page that can be created/customized in admin.
    https://docs.djangoproject.com/en/3.2/ref/contrib/flatpages/

    fields: title, draft_title, slug, depth, live, go_live_at...
    """

    meta_title = models.CharField(
        verbose_name="Titre (balise meta)",
        max_length=100,
        blank=True,
        default="",
        help_text=(
            "Le titre qui sera affiché dans les SERPs. "
            "Il est recommandé de le garder < 60 caractères. "
            "Laissez vide pour réutiliser le titre de la page."
        ),
    )
    meta_description = models.TextField(
        verbose_name="Description (balise meta)",
        max_length=255,
        blank=True,
        default="",
        help_text="La description qui sera affichée dans les SERPs. À garder < 150 caractères.",
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)


class PagePartial(models.Model):
    title = models.CharField(verbose_name="Titre", max_length=255, unique=True)
    content = models.TextField(verbose_name="Contenu", blank=True)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
