from django.db import models
from django.utils import timezone


class Purchase(models.Model):
    """
    Model to store purchase data imported from CSV files.
    Links to SIAE if the SIRET matches an existing SIAE.
    """

    # Supplier information
    supplier_name = models.CharField(
        verbose_name="Raison sociale du Fournisseur", max_length=255, help_text="Nom de l'entreprise fournisseur"
    )
    supplier_siret = models.CharField(
        verbose_name="SIRET du Fournisseur", max_length=14, help_text="Numéro SIRET du fournisseur (14 chiffres)"
    )

    # Purchase information
    purchase_amount = models.DecimalField(
        verbose_name="Dépense achat (€)", max_digits=15, decimal_places=2, help_text="Montant de l'achat en euros"
    )
    purchase_category = models.CharField(
        verbose_name="Catégorie d'achat",
        max_length=255,
        blank=True,
        null=True,
        help_text="Catégorie d'achat (optionnelle)",
    )
    buying_entity = models.CharField(
        verbose_name="Entité acheteuse",
        max_length=255,
        blank=True,
        null=True,
        help_text="Entité acheteuse (optionnelle)",
    )
    company = models.ForeignKey(
        "companies.Company",
        verbose_name="Entreprise",
        on_delete=models.CASCADE,
        help_text="Entreprise liée à l'achat",
    )

    # Year of purchase
    purchase_year = models.PositiveIntegerField(
        verbose_name="Année de l'achat", help_text="Année de réalisation de l'achat"
    )

    # Link to SIAE if SIRET matches
    siae = models.ForeignKey(
        "siaes.Siae",
        verbose_name="Structure d'insertion",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Structure d'insertion liée si le SIRET correspond",
    )

    # Metadata
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        indexes = [
            models.Index(fields=["supplier_siret"]),
            models.Index(fields=["purchase_year"]),
            models.Index(fields=["siae"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"{self.supplier_name} - {self.purchase_amount}€ ({self.purchase_year})"
