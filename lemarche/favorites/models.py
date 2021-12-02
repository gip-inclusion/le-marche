from uuid import uuid4

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class FavoriteList(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur", related_name="favorite_lists", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Liste de favoris"
        verbose_name_plural = "Listes de favoris"

    def __str__(self):
        return self.name

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = f"{slugify(self.name)[:40]}-{str(uuid4())[:4]}"

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)
