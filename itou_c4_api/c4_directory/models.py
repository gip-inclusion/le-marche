from django.db import models
from django.utils import timezone

## Temporary code
## FIXME : move elsewhere
from django.core.exceptions import ValidationError
def validate_siret(siret):
    if not siret.isdigit() or len(siret) != 14:
        raise ValidationError("Le numéro SIRET doit être composé de 14 chiffres.")

def validate_naf(naf):
    if len(naf) != 5 or not naf[:4].isdigit() or not naf[4].isalpha():
        raise ValidationError("Le code NAF doit être composé de de 4 chiffres et d'une lettre.")
## End of temporary code


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
    createdat = models.DateTimeField(verbose_name="Date de création", default=timezone.now)

    class Meta:
        ordering = ['name']

    # latitude
    # longitude
    # creation_date
    # workers_count
    # prestation_types
    # sectors
    # phone ?
    # email ?
