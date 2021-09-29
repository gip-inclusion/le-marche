# https://github.com/betagouv/itou/blob/master/itou/cities/models.py

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
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
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)

    kind = models.CharField(verbose_name="Type de structure", max_length=20, choices=KIND_CHOICES)
    insee_code = models.CharField(verbose_name="Code INSEE", max_length=5, unique=True)

    # only for cities
    # Latitude and longitude coordinates.
    # https://docs.djangoproject.com/en/2.2/ref/contrib/gis/model-api/#pointfield
    coords = gis_models.PointField(geography=True, blank=True, null=True)
    post_codes = ArrayField(models.CharField(max_length=5), verbose_name="Codes postaux", blank=True, null=True)
    department_code = models.CharField(
        verbose_name="Département", choices=DEPARTMENT_CHOICES, max_length=3, blank=True, null=True
    )
    population = models.IntegerField(verbose_name="Population", blank=True, null=True)

    # only for cities & departments
    region_code = models.CharField(verbose_name="Région", choices=REGION_CHOICES, max_length=2, blank=True, null=True)

    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Périmètre"
        verbose_name_plural = "Périmètres"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        if self.kind == self.KIND_CITY:
            return f"{self.name} ({self.department})"
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
