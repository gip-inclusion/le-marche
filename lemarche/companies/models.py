from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    description = models.TextField(verbose_name="Description", blank=True)
    website = models.URLField(verbose_name="Site web", blank=True)
    logo_url = models.URLField(verbose_name="Lien vers le logo", max_length=500, blank=True)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

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
