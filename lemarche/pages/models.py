from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.utils import timezone


class Page(FlatPage):
    """
    A static page that can be created/customized in admin.
    https://docs.djangoproject.com/en/3.2/ref/contrib/flatpages/

    fields: title, url, content...
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


class PageFragment(models.Model):
    title = models.CharField(verbose_name="Titre", max_length=255, unique=True)
    content = models.TextField(verbose_name="Contenu", blank=True)

    is_live = models.BooleanField(
        verbose_name="Visible", default=True, help_text="Laisser vide pour cacher le contenu dans l'application"
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Fragment de page"
        verbose_name_plural = "Fragments de page"
        ordering = ["title"]

    def __str__(self):
        return self.title
