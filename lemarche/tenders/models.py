import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# Create your models here.
class Tender(models.Model):
    """Appel d'offre et devis"""

    TENDERS_KIND_TENDER = "TENDER"
    TENDERS_KIND_QUOTE = "QUOTE"
    TENDERS_KIND_BOAMP = "BOAMP"

    TENDERS_KIND_CHOICES = (
        (TENDERS_KIND_TENDER, "Appel d'offre"),
        (TENDERS_KIND_QUOTE, "Devis"),
    )

    RESPONSES_KIND_EMAIL = "EMAIL"
    RESPONSES_KIND_TEL = "TEL"
    RESPONSES_KIND_EXTERNAL = "EXTERN"

    RESPONSES_KIND_CHOICES = (
        (RESPONSES_KIND_EMAIL, "Email"),
        (RESPONSES_KIND_EMAIL, "Téléphone"),
        (RESPONSES_KIND_EMAIL, "Lien externe"),
    )

    kind = models.CharField(
        verbose_name="Type de besoin", max_length=6, choices=TENDERS_KIND_CHOICES, default=TENDERS_KIND_TENDER
    )

    title = models.CharField(verbose_name="Titre", max_length=255)
    description = models.TextField(verbose_name="Description", blank=True)
    constraints = models.TextField(verbose_name="Contraintes techniques spécifiques", blank=True)
    completion_time = models.TextField(verbose_name="Délais de réalisation / Fréquence", blank=True)
    external_link = models.URLField(verbose_name="Lien externe", blank=True)
    deadline_date = models.DateField(verbose_name="Date de clôture des réponses")
    start_working_date = models.DateField(verbose_name="Date idéale de début des prestations", blank=True, null=True)
    response_kind = models.CharField(
        verbose_name="Comment répondre", max_length=6, choices=RESPONSES_KIND_CHOICES, default=RESPONSES_KIND_EMAIL
    )

    perimeters = models.ManyToManyField(
        "perimeters.Perimeter", verbose_name="Lieux d'exécutions", related_name="tenders", blank=True
    )
    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activités", related_name="tenders", blank=True
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Besoin d'acheteur"
        verbose_name_plural = "Besoins des acheteurs"
        ordering = ["deadline_date"]

    def clean(self):
        today = datetime.date.today()

        if self.deadline_date < today:
            raise ValidationError("La date de cloture des réponses ne doit pas être antérieure à aujourd'hui.")

        if self.start_working_date and self.start_working_date < self.deadline_date:
            raise ValidationError(
                "La date idéale de début des prestations ne doit pas être antérieure de cloture des réponses."
            )

    def __str__(self):
        return self.title
