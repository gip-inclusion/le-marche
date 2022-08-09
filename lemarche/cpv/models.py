from django.db import models
from django.utils import timezone


class Code(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    code = models.CharField(verbose_name="Code", max_length=8)

    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activité", related_name="cpv_codes", blank=True
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Code CPV"
        verbose_name_plural = "Code CPV"
        ordering = ["code"]
