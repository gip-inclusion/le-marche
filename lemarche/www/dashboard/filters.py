import django_filters
from django import forms

from lemarche.purchases.models import Purchase
from lemarche.siaes.constants import KIND_CHOICES_WITH_EXTRA, KIND_HANDICAP_LIST, KIND_INSERTION_LIST


def get_purchase_category_choices():
    purchase_categories = Purchase.objects.values_list("purchase_category", flat=True).distinct()
    return [(purchase_category, purchase_category) for purchase_category in purchase_categories]


def get_buying_entities_choices():
    buying_entities = Purchase.objects.values_list("buying_entity", flat=True).distinct()
    return [(buying_entity, buying_entity) for buying_entity in buying_entities]


class PurchaseFilterSet(django_filters.FilterSet):
    INCLUSIVE_SECTOR_TYPE_CHOCIES = ((KIND_INSERTION_LIST, "Insertion"), (KIND_HANDICAP_LIST, "Handicap"))
    #
    # inclusive_sector_type = django_filters.MultipleChoiceFilter(
    #     label="Type de secteur inclusif",
    #     widget=forms.CheckboxSelectMultiple,
    #     field_name="siae__kind",
    #     lookup_expr="in",
    #     choices=INCLUSIVE_SECTOR_TYPE_CHOCIES,
    # )
    siae_type = django_filters.MultipleChoiceFilter(
        label="Type de structure",
        widget=forms.CheckboxSelectMultiple,
        method="filter_siae_type",
        choices=KIND_CHOICES_WITH_EXTRA,
    )
    purchase_category = django_filters.MultipleChoiceFilter(
        choices=get_purchase_category_choices(), widget=forms.CheckboxSelectMultiple
    )
    buying_entity = django_filters.MultipleChoiceFilter(
        choices=get_buying_entities_choices(), widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Purchase
        fields = ["siae_type", "purchase_category", "buying_entity"]

    def filter_siae_type(self, queryset, name, value):
        """Return departement by provided code or name"""
        return queryset.filter(siae__kind__in=value)
