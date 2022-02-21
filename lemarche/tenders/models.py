from django.db import models


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
    deadline_date = models.DateField(verbose_name="Date de clôture des réponses", blank=True, null=True)
    start_working_date = models.DateField(verbose_name="Date idéale de début des prestations", blank=True, null=True)
    kind_response = models.CharField(
        verbose_name="Comment répondre", max_length=6, choices=KIND_RESPONSES_CHOICES, default=KIND_TENDERS_TENDER
    )

    perimeters = models.ManyToManyField(
        "perimeters.Perimeter", verbose_name="Lieu d'exécution", related_name="tenders", blank=True
    )
    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activité", related_name="tenders", blank=True
    )
