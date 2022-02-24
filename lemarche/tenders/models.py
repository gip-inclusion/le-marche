import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# Create your models here.
class Tender(models.Model):
    """Appel d'offre et devis"""

    KIND_TENDERS_TENDER = "TENDER"
    KIND_TENDERS_QUOTE = "QUOTE"
    KIND_TENDERS_BOAMP = "BOAMP"

    KIND_TENDERS_CHOICES = (
        (KIND_TENDERS_TENDER, "Appel d'offre"),
        (KIND_TENDERS_QUOTE, "Devis"),
    )

    KIND_RESPONSES_EMAIL = "EMAIL"
    KIND_RESPONSES_TEL = "TEL"
    KIND_RESPONSES_EXTERNAL = "EXTERN"

    KIND_RESPONSES_CHOICES = (
        (KIND_RESPONSES_EMAIL, "Email"),
        (KIND_RESPONSES_EMAIL, "Téléphone"),
        (KIND_RESPONSES_EMAIL, "Lien externe"),
    )

    kind = models.CharField(
        verbose_name="Type de besoin", max_length=6, choices=KIND_TENDERS_CHOICES, default=KIND_TENDERS_TENDER
    )

    title = models.CharField(verbose_name="Titre", max_length=255)
    description = models.TextField(verbose_name="Description", blank=True)
    constraints = models.TextField(verbose_name="Contraintes techniques spécifiques", blank=True)
    completion_time = models.TextField(verbose_name="Délais de réalisation / Fréquence", blank=True)
    external_link = models.URLField(verbose_name="Lien externe", blank=True)
    deadline_date = models.DateField(verbose_name="Date de clôture des réponses")
    start_working_date = models.DateField(verbose_name="Date idéale de début des prestations", blank=True, null=True)
    kind_response = models.CharField(
        verbose_name="Comment répondre", max_length=6, choices=KIND_RESPONSES_CHOICES, default=KIND_TENDERS_TENDER
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
            raise ValidationError("La date de cloture des réponses ne doit pas être antérieur à aujourd'hui.")

        if self.start_working_date and self.start_working_date < self.deadline_date:
            raise ValidationError(
                "La date idéale de début de préstation ne doit pas être antérieur de cloture des réponses."
            )

    def __str__(self):
        return self.title
