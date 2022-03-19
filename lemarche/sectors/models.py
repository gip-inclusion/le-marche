from django.db import models
from django.db.models import Value
from django.db.models.functions import NullIf
from django.template.defaultfilters import slugify
from django.utils import timezone


class SectorGroup(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Groupe de secteurs d'activité"
        verbose_name_plural = "Groupes de secteurs d'activité"
        ordering = ["name"]

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


class SectorQuerySet(models.QuerySet):
    def form_filter_queryset(self):
        """
        In our filter forms, we want to display the sectors by group.
        """
        return (
            self.select_related("group")
            .exclude(group=None)  # sector must have a group !
            .annotate(sector_is_autre=NullIf("name", Value("Autre")))
            .order_by("group__id", "sector_is_autre")
        )


class Sector(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    group = models.ForeignKey(
        "SectorGroup",
        verbose_name="Groupe parent",
        related_name="sectors",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(SectorQuerySet)()

    class Meta:
        verbose_name = "Secteur d'activité"
        verbose_name_plural = "Secteurs d'activité"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = slugify(self.name)[:50]
            if self.name == "Autre":
                self.slug += f"-{slugify(self.group.name)[:50]}"

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)
