from django.db import models


# Create your models here.
class Tender(models.Model):
    """Appel d'offre et devis
    - Type* (*kind*) : (Devis, Appel d’offre)
    - Titre* (*title*)
    - Description* (*description*)
    - Secteur d’activité* : plusieurs secteurs ?
    - Contraintes techniques spécifiques*
    - Délais de réalisation / Fréquence*
    - Lieu d’exécution* : *un seul ou plusieurs ?*
    - Lien externe (*external_link) :
    - Cordonnées de contacts* : Est-ce qu’on reprends les mêmes que celle de la structure qui fait la demande ?
    - Comment répondre ?* : List de choix (email, tel, external_link)

    """

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

    KIND_TENDERS_CHOICES = (
        (KIND_RESPONSES_EMAIL, "Email"),
        (KIND_RESPONSES_EMAIL, "Téléphone"),
        (KIND_RESPONSES_EMAIL, "Lien externe"),
    )

    kind = models.CharField(
        verbose_name="Type de besoin", max_length=6, choices=KIND_TENDERS_CHOICES, default=KIND_TENDERS_TENDER
    )

    title = models.CharField(verbose_name="Titre", max_length=255)
    description = models.TextField(verbose_name="Description", blank=True)

    # secteur d'activité
    sector = models.ForeignKey("sectors.Sector", verbose_name="Secteur d'activité", on_delete=models.DO_NOTHING)

    constraints = models.TextField(verbose_name="Contraintes techniques spécifiques", blank=True)
    completion_time = models.TextField(verbose_name="Délais de réalisation / Fréquence", blank=True)

    # lieu d'exécution
    perimeter = models.ForeignKey("perimeters.Perimeter", verbose_name="Lieu d'exécution", on_delete=models.DO_NOTHING)

    external_link = models.URLField(verbose_name="Lien externe", blank=True)

    kind_response = models.CharField(
        verbose_name="Comment répondre", max_length=6, choices=KIND_TENDERS_CHOICES, default=KIND_TENDERS_TENDER
    )
