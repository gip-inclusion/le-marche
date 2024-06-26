from django.db import models
from django.db.models import Count
from django.template.defaultfilters import slugify
from django.utils import timezone


class NetworkQuerySet(models.QuerySet):
    def with_siae_stats(self):
        return self.annotate(siae_count_annotated=Count("siaes", distinct=True))

    def with_user_partner_stats(self):
        return self.annotate(user_partner_count_annotated=Count("user_partners", distinct=True))


class Network(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    brand = models.CharField(verbose_name="Enseigne", max_length=255, blank=True)
    website = models.URLField(verbose_name="Site web", blank=True)
    logo_url = models.URLField(verbose_name="Lien vers le logo", max_length=500, blank=True)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(NetworkQuerySet)()

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
