from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class Network(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    brand = models.CharField(verbose_name="Enseigne", max_length=255, blank=True)
    website = models.URLField(verbose_name="Site web", blank=True)
    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Réseau"
        verbose_name_plural = "Réseaux"

    def __str__(self):
        return self.name

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = slugify(self.name)[:50]

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)
