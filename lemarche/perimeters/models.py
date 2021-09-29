# https://github.com/betagouv/itou/blob/master/itou/cities/models.py
# code_insee --> insee_code

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from lemarche.siaes.constants import DEPARTMENTS, REGIONS_WITH_CODES


class Perimeter(models.Model):
    KIND_CITY = "CITY"
    KIND_DEPARTMENT = "DEPARTMENT"
    KIND_REGION = "REGION"
    KIND_CHOICES = (
        (KIND_CITY, "Commune"),
        (KIND_DEPARTMENT, "Département"),
        (KIND_REGION, "Région"),
    )
    DEPARTMENT_CHOICES = DEPARTMENTS.items()
    REGION_CHOICES = REGIONS_WITH_CODES.items()

    name = models.CharField(verbose_name="Nom", max_length=255, db_index=True)
    # Note: some REGIONS have the same name as a DEPARTMENT. So we add '-region' at their end
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)

    kind = models.CharField(verbose_name="Type de périmètre", max_length=20, choices=KIND_CHOICES)
    # Note: REGION insee_codes are prefixed with a 'R' to avoid conflicts with DEPARTMENT
    insee_code = models.CharField(verbose_name="Code INSEE", max_length=5, unique=True)

    # only for cities
    # Latitude and longitude coordinates.
    # https://docs.djangoproject.com/en/2.2/ref/contrib/gis/model-api/#pointfield
    coords = gis_models.PointField(geography=True, blank=True, null=True)
    post_codes = ArrayField(models.CharField(max_length=5), verbose_name="Codes postaux", blank=True, null=True)
    department_code = models.CharField(
        verbose_name="Département (code)", choices=DEPARTMENT_CHOICES, max_length=3, blank=True, null=True
    )
    population = models.IntegerField(verbose_name="Population", blank=True, null=True)

    # only for cities & departments
    region_code = models.CharField(
        verbose_name="Région (code)", choices=REGION_CHOICES, max_length=2, blank=True, null=True
    )

    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Périmètre"
        verbose_name_plural = "Périmètres"
        indexes = [
            # https://docs.djangoproject.com/en/dev/ref/contrib/postgres/search/#trigram-similarity
            # https://docs.djangoproject.com/en/dev/ref/contrib/postgres/indexes/#ginindex
            # https://www.postgresql.org/docs/11/pgtrgm.html#id-1.11.7.40.7
            GinIndex(fields=["name"], name="perimeters_name_gin_trgm", opclasses=["gin_trgm_ops"])
        ]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        if self.kind == self.KIND_CITY:
            return f"{self.name} ({self.department_code})"
        return self.name

    @property
    def latitude(self):
        if self.coords:
            return self.coords.y
        return None

    @property
    def longitude(self):
        if self.coords:
            return self.coords.x
        return None
