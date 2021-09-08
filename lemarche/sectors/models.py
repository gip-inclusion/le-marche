from django.db import models
from django.utils import timezone


class SectorGroup(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Groupe de secteurs d'activité"
        verbose_name_plural = "Groupes de secteurs d'activité"

    def __str__(self):
        return self.name


class Sector(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    group = models.ForeignKey(
        "SectorGroup",
        verbose_name="Groupe parent",
        related_name='sectors',
        on_delete=models.SET_NULL,
        null=True, blank=True)
    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Secteur d'activité"
        verbose_name_plural = "Secteurs d'activité"

    def __str__(self):
        return self.name
