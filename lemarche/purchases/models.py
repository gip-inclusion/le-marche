from django.db import models
from django.db.models import Count, ExpressionWrapper, IntegerField, Q, Sum
from django.db.models.functions import Coalesce, Round
from django.utils import timezone
from django.utils.text import slugify

from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.users.models import User


class PurchaseQuerySet(models.QuerySet):
    def get_purchase_for_user(self, user: User):
        return self.filter(company=user.company)

    def with_stats(self):
        aggregates = {
            "total_amount_annotated": ExpressionWrapper(
                Coalesce(Round(Sum("purchase_amount"), 0), 0),
                output_field=IntegerField(),
            ),
            "total_inclusive_amount_annotated": ExpressionWrapper(
                Coalesce(Round(Sum("purchase_amount", filter=Q(siae__isnull=False)), 0), 0),
                output_field=IntegerField(),
            ),
            "total_insertion_amount_annotated": ExpressionWrapper(
                Coalesce(Round(Sum("purchase_amount", filter=Q(siae__kind__in=KIND_INSERTION_LIST)), 0), 0),
                output_field=IntegerField(),
            ),
            "total_handicap_amount_annotated": ExpressionWrapper(
                Coalesce(Round(Sum("purchase_amount", filter=Q(siae__kind__in=KIND_HANDICAP_LIST)), 0), 0),
                output_field=IntegerField(),
            ),
            "total_suppliers_annotated": Count("supplier_siret", distinct=True),
            "total_inclusive_suppliers_annotated": Count(
                "supplier_siret", filter=Q(siae__isnull=False), distinct=True
            ),
        }

        # get sum of purchases by siae__kind
        for kind in KIND_INSERTION_LIST + KIND_HANDICAP_LIST:
            aggregates[f"total_purchases_by_kind_{kind}"] = ExpressionWrapper(
                Coalesce(Round(Sum("purchase_amount", filter=Q(siae__kind=kind)), 0), 0),
                output_field=IntegerField(),
            )

        # QPV / ZRR breakdown (4 segments: QPV only, ZRR only, both, neither)
        aggregates["total_purchases_qpv_only"] = ExpressionWrapper(
            Coalesce(
                Round(
                    Sum(
                        "purchase_amount",
                        filter=Q(siae__isnull=False, siae__is_qpv=True, siae__is_zrr=False),
                    ),
                    0,
                ),
                0,
            ),
            output_field=IntegerField(),
        )
        aggregates["total_purchases_zrr_only"] = ExpressionWrapper(
            Coalesce(
                Round(
                    Sum(
                        "purchase_amount",
                        filter=Q(siae__isnull=False, siae__is_qpv=False, siae__is_zrr=True),
                    ),
                    0,
                ),
                0,
            ),
            output_field=IntegerField(),
        )
        aggregates["total_purchases_qpv_and_zrr"] = ExpressionWrapper(
            Coalesce(
                Round(
                    Sum(
                        "purchase_amount",
                        filter=Q(siae__isnull=False, siae__is_qpv=True, siae__is_zrr=True),
                    ),
                    0,
                ),
                0,
            ),
            output_field=IntegerField(),
        )
        aggregates["total_purchases_no_qpv_no_zrr"] = ExpressionWrapper(
            Coalesce(
                Round(
                    Sum(
                        "purchase_amount",
                        filter=Q(siae__isnull=False, siae__is_qpv=False, siae__is_zrr=False),
                    ),
                    0,
                ),
                0,
            ),
            output_field=IntegerField(),
        )

        # get sum of purchases by purchases category
        for category in (
            self.filter(siae__isnull=False)
            .values_list("purchase_category", flat=True)
            .order_by("purchase_category")
            .distinct()
        ):
            category_key = slugify(category)
            aggregates[f"total_purchases_by_category_{category_key}"] = ExpressionWrapper(
                Coalesce(
                    Round(Sum("purchase_amount", filter=Q(purchase_category=category, siae__isnull=False)), 0), 0
                ),
                output_field=IntegerField(),
            )

        for buying_entity in (
            self.filter(siae__isnull=False)
            .values_list("buying_entity", flat=True)
            .order_by("buying_entity")
            .distinct()
        ):
            buying_entity_key = slugify(buying_entity)
            aggregates[f"total_purchases_by_buying_entity_{buying_entity_key}"] = ExpressionWrapper(
                Coalesce(
                    Round(Sum("purchase_amount", filter=Q(buying_entity=buying_entity, siae__isnull=False)), 0), 0
                ),
                output_field=IntegerField(),
            )

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
            models.Index(fields=["purchase_category"]),
            models.Index(fields=["buying_entity"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.supplier_name} - {self.purchase_amount}€ ({self.purchase_year})"
