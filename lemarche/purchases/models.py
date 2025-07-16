from django.db import models
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Round
from django.utils import timezone

from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.users.models import User


class PurchaseQuerySet(models.QuerySet):
    def get_purchase_for_user(self, user: User):
        return self.filter(company=user.company)

    def with_stats(self):
        aggregates = {
            "total_amount_annotated": Sum("purchase_amount"),
            "total_inclusive_amount_annotated": Sum("purchase_amount", filter=Q(siae__isnull=False)),
            "total_inclusive_percentage_annotated": ExpressionWrapper(
                Round(F("total_inclusive_amount_annotated") / F("total_amount_annotated") * 100, 2),
                output_field=DecimalField(max_digits=5, decimal_places=2),
            ),
            "total_insertion_amount_annotated": Sum("purchase_amount", filter=Q(siae__kind__in=KIND_INSERTION_LIST)),
            "total_handicap_amount_annotated": Sum("purchase_amount", filter=Q(siae__kind__in=KIND_HANDICAP_LIST)),
            "total_insertion_percentage_annotated": ExpressionWrapper(
                Round(F("total_insertion_amount_annotated") / F("total_amount_annotated") * 100, 2),
                output_field=DecimalField(max_digits=5, decimal_places=2),
            ),
            "total_handicap_percentage_annotated": ExpressionWrapper(
                Round(F("total_handicap_amount_annotated") / F("total_amount_annotated") * 100, 2),
                output_field=DecimalField(max_digits=5, decimal_places=2),
            ),
            "total_suppliers_annotated": Count("supplier_siret", distinct=True),
            "total_inclusive_suppliers_annotated": Count(
                "supplier_siret", filter=Q(siae__isnull=False), distinct=True
            ),
        }

        # get sum of purchases by siae__kind
        for kind in KIND_INSERTION_LIST + KIND_HANDICAP_LIST:
            aggregates[f"total_purchases_by_kind_{kind}"] = Sum("purchase_amount", filter=Q(siae__kind=kind))

        return self.aggregate(**aggregates)


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

    objects = models.Manager.from_queryset(PurchaseQuerySet)()

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        indexes = [
            models.Index(fields=["supplier_siret"]),
            models.Index(fields=["purchase_year"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.supplier_name} - {self.purchase_amount}€ ({self.purchase_year})"
