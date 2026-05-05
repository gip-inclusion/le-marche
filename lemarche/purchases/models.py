from collections import defaultdict
from decimal import Decimal

from django.db import models
from django.db.models import Case, CharField, Count, ExpressionWrapper, F, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce, Round
from django.utils import timezone
from django.utils.text import slugify

from lemarche.purchases import constants as purchases_constants
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

    def with_size_stats(self):
        """
        Purchase amounts and supplier counts grouped by size category.

        TPE: total employees < 10
        PME: total employees >= 10
        Non renseigné: insertion count, c2_etp_count and permanent count all null

        Effective insertion = employees_insertion_count ?? round(c2_etp_count)
        Total employees = effective_insertion + permanent_count (nulls treated as 0)
        """
        SIZE_NON_RENSEIGNE = "Non renseigné"
        SIZE_TPE = "TPE (< 10 salariés)"
        SIZE_PME = "PME (≥ 10 salariés)"

        qs = (
            self.filter(siae__isnull=False)
            .annotate(
                _eff_insertion=Case(
                    When(
                        siae__employees_insertion_count__isnull=False,
                        then=F("siae__employees_insertion_count"),
                    ),
                    When(
                        siae__c2_etp_count__isnull=False,
                        then=Round(F("siae__c2_etp_count")),
                    ),
                    default=Value(None, output_field=IntegerField()),
                    output_field=IntegerField(),
                )
            )
            .annotate(
                _total_employees=Case(
                    When(
                        _eff_insertion__isnull=True,
                        siae__employees_permanent_count__isnull=True,
                        then=Value(None, output_field=IntegerField()),
                    ),
                    default=ExpressionWrapper(
                        Coalesce(F("_eff_insertion"), Value(0))
                        + Coalesce(F("siae__employees_permanent_count"), Value(0)),
                        output_field=IntegerField(),
                    ),
                    output_field=IntegerField(),
                )
            )
            .annotate(
                size_category=Case(
                    When(_total_employees__isnull=True, then=Value(SIZE_NON_RENSEIGNE)),
                    When(_total_employees__lt=10, then=Value(SIZE_TPE)),
                    default=Value(SIZE_PME),
                    output_field=CharField(),
                )
            )
        )

        return (
            qs.values("size_category")
            .annotate(
                total_amount=ExpressionWrapper(
                    Coalesce(Round(Sum("purchase_amount"), 0), Value(0)),
                    output_field=IntegerField(),
                ),
                supplier_count=Count("supplier_siret", distinct=True),
            )
            .order_by("size_category")
        )

    def with_legal_form_stats(self):
        """
        Purchase amounts and supplier counts grouped by siae legal form.
        Results ordered by total amount descending.
        """
        return (
            self.filter(siae__isnull=False)
            .values("siae__legal_form")
            .annotate(
                total_amount=ExpressionWrapper(
                    Coalesce(Round(Sum("purchase_amount"), 0), Value(0)),
                    output_field=IntegerField(),
                ),
                supplier_count=Count("supplier_siret", distinct=True),
            )
            .order_by("-total_amount")
        )

    def with_region_stats(self):
        """
        Purchase amounts and supplier counts grouped by siae region.
        Results ordered by total amount descending.
        """
        return (
            self.filter(siae__isnull=False)
            .values("siae__region")
            .annotate(
                total_amount=ExpressionWrapper(
                    Coalesce(Round(Sum("purchase_amount"), 0), Value(0)),
                    output_field=IntegerField(),
                ),
                supplier_count=Count("supplier_siret", distinct=True),
            )
            .order_by("-total_amount")
        )


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


def get_sector_group_chart_data(queryset, top_n=10):
    """
    Returns chart data for inclusive purchases by sector group, using fractional attribution.

    For each inclusive purchase, the amount is split equally across the distinct SectorGroups
    of the matched SIAE (e.g. a SIAE in 2 groups → 50% to each). This prevents the total
    from exceeding the real inclusive spend.

    Returns a dict with keys: labels, amounts, supplier_counts.
    """
    # Query 1 — distinct (siae_id, group_name) pairs for SIAEs in this queryset
    siae_group_rows = (
        queryset.filter(siae__isnull=False, siae__activities__sector__group__isnull=False)
        .values("siae_id", "siae__activities__sector__group__name")
        .distinct()
    )
    siae_groups: dict[int, set[str]] = defaultdict(set)
    for row in siae_group_rows:
        siae_groups[row["siae_id"]].add(row["siae__activities__sector__group__name"])

    if not siae_groups:
        return {"labels": [], "amounts": [], "supplier_counts": []}

    # Query 2 — all inclusive purchases
    purchase_rows = queryset.filter(siae__isnull=False).values("purchase_amount", "supplier_siret", "siae_id")

    sector_amounts: dict[str, Decimal] = defaultdict(Decimal)
    sector_suppliers: dict[str, set[str]] = defaultdict(set)

    for row in purchase_rows:
        groups = siae_groups.get(row["siae_id"])
        if not groups:
            continue
        fraction = Decimal(row["purchase_amount"]) / len(groups)
        for group_name in groups:
            sector_amounts[group_name] += fraction
            sector_suppliers[group_name].add(row["supplier_siret"])

    if not sector_amounts:
        return {"labels": [], "amounts": [], "supplier_counts": []}

    sorted_sectors = sorted(sector_amounts.items(), key=lambda x: x[1], reverse=True)
    top = sorted_sectors[:top_n]
    others = sorted_sectors[top_n:]

    labels = [name for name, _ in top]
    amounts = [int(round(amount)) for _, amount in top]
    supplier_counts = [len(sector_suppliers[name]) for name, _ in top]

    if others:
        labels.append("Autres")
        amounts.append(int(round(sum(amount for _, amount in others))))
        other_suppliers: set[str] = set()
        for name, _ in others:
            other_suppliers.update(sector_suppliers[name])
        supplier_counts.append(len(other_suppliers))

    return {"labels": labels, "amounts": amounts, "supplier_counts": supplier_counts}


class SlugMappingCacheQuerySet(models.QuerySet):
    def validated(self):
        return self.filter(source=purchases_constants.SLUG_MAPPING_SOURCE_ADMIN_VALIDATED)

    def pending(self):
        return self.filter(source=purchases_constants.SLUG_MAPPING_SOURCE_USER_PROPOSED)

    def for_kind(self, kind: str):
        return self.filter(kind=kind)


class SlugMappingCache(models.Model):
    """
    Base de correspondances entre valeurs saisies librement dans l'Excel
    et slugs internes (secteurs, périmètres, en-têtes de colonnes).

    Alimentée par les validations utilisateurs, modérée par l'admin.
    Les entrées admin_validated sont utilisées en priorité pour tous les utilisateurs.
    """

    raw_value = models.CharField(verbose_name="Valeur saisie", max_length=255, db_index=True)
    kind = models.CharField(
        verbose_name="Type",
        max_length=30,
        choices=purchases_constants.SLUG_MAPPING_KIND_CHOICES,
    )
    resolved_slug = models.CharField(verbose_name="Slug résolu", max_length=255)
    source = models.CharField(
        verbose_name="Source",
        max_length=30,
        choices=purchases_constants.SLUG_MAPPING_SOURCE_CHOICES,
        default=purchases_constants.SLUG_MAPPING_SOURCE_USER_PROPOSED,
    )
    confidence = models.FloatField(verbose_name="Score de confiance", default=1.0)
    usage_count = models.PositiveIntegerField(verbose_name="Nombre d'utilisations", default=1)
    proposed_by = models.ForeignKey(
        User,
        verbose_name="Proposé par",
        related_name="slug_mapping_proposals",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    validated_by = models.ForeignKey(
        User,
        verbose_name="Validé par",
        related_name="slug_mapping_validations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    validated_at = models.DateTimeField(verbose_name="Date de validation", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(SlugMappingCacheQuerySet)()

    class Meta:
        verbose_name = "Correspondance de matching"
        verbose_name_plural = "Correspondances de matching"
        unique_together = [("raw_value", "kind")]
        ordering = ["-usage_count", "raw_value"]

    def __str__(self) -> str:
        return f"« {self.raw_value} » → {self.resolved_slug} ({self.get_kind_display()})"
