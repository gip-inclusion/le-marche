from django.db import models
from django.db.models import Count
from django.template.defaultfilters import slugify
from django.utils import timezone


class LabelQuerySet(models.QuerySet):
    def with_siae_stats(self):
        return self.annotate(siae_count_annotated=Count("siaes", distinct=True))


class Label(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    description = models.TextField(verbose_name="Description", blank=True)
    website = models.URLField(verbose_name="Site web", blank=True)
    logo_url = models.URLField(verbose_name="Lien vers le logo", max_length=500, blank=True)

    data_description = models.TextField(verbose_name="Description de la source de données", blank=True)
    data_last_sync_date = models.DateTimeField("Date de dernière synchronisation", blank=True, null=True)

    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(LabelQuerySet)()

    class Meta:
        verbose_name = "Label & certification"
        verbose_name_plural = "Labels & certifications"

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

    @property
    def has_logo(self):
        return len(self.logo_url) > 0
