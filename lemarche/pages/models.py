from django.db import models
from django.utils import timezone
from django.contrib.flatpages.models import FlatPage


class Page(FlatPage):
    """
    A static page that can be created/customized in admin.
    https://docs.djangoproject.com/en/3.2/ref/contrib/flatpages/
    """

    meta_title = models.CharField(
        "Titre (balise meta)",
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
        "Description (balise meta)",
        max_length=255,
        blank=True,
        default="",
        help_text=("La description qui sera affichée dans les SERPs. " "À garder < 150 caractères."),
    )

    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)
