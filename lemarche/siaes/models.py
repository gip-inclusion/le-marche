from django.db import models
from django.utils import timezone

from lemarche.siaes.validators import validate_siret, validate_naf
from lemarche.api.models import Sector


class Siae(models.Model):
    KIND_EI = "EI"
    KIND_AI = "AI"
    KIND_ACI = "ACI"
    KIND_ETTI = "ETTI"
    KIND_EITI = "EITI"
    KIND_GEIQ = "GEIQ"
    KIND_EA = "EA"
    KIND_EATT = "EATT"

    KIND_CHOICES = (
        (KIND_EI, "Entreprise d'insertion"),  # Regroupées au sein de la fédération des entreprises d'insertion.
        (KIND_AI, "Association intermédiaire"),
        (KIND_ACI, "Atelier chantier d'insertion"),
        # (KIND_ACIPHC, "Atelier chantier d'insertion premières heures en chantier"),
        (KIND_ETTI, "Entreprise de travail temporaire d'insertion"),
        (KIND_EITI, "Entreprise d'insertion par le travail indépendant"),
        (KIND_GEIQ, "Groupement d'employeurs pour l'insertion et la qualification"),
        (KIND_EA, "Entreprise adaptée"),
        (KIND_EATT, "Entreprise adaptée de travail temporaire"),
    )

    name = models.CharField(verbose_name="Nom", max_length=255)
    brand = models.CharField(verbose_name="Enseigne", max_length=255, blank=True)
    kind = models.CharField(verbose_name="Type", max_length=6, choices=KIND_CHOICES, default=KIND_EI)
    siret = models.CharField(verbose_name="Siret", max_length=14, validators=[validate_siret], db_index=True)
    naf = models.CharField(verbose_name="Naf", max_length=5, validators=[validate_naf], blank=True)
    address = models.TextField(verbose_name="Adresse")
    website = models.URLField(verbose_name="Site web", blank=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    post_code = models.CharField(max_length=255, blank=True, null=True)
    is_qpv = models.BooleanField(verbose_name="Zone QPV", blank=False, null=False, default=False)
    sectors = models.ManyToManyField(Sector)
    createdat = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updatedat = models.DateTimeField(verbose_name="Date de mise à jour", default=timezone.now)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("access_api", "Can acces the API"),
        ]
