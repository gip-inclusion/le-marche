import django_filters
from django import forms

from lemarche.purchases.models import Purchase


def get_purchase_category_choices():
    purchase_categories = Purchase.objects.values_list("purchase_category", flat=True).distinct()
    return [(purchase_category, purchase_category) for purchase_category in purchase_categories]


def get_buying_entities_choices():
    buying_entities = Purchase.objects.values_list("buying_entity", flat=True).distinct()
    return [(buying_entity, buying_entity) for buying_entity in buying_entities]


class PurchaseFilterSet(django_filters.FilterSet):
    inclusive_sector_type = ...
    siae_type = ...
    purchase_category = django_filters.MultipleChoiceFilter(
        choices=get_purchase_category_choices(), widget=forms.CheckboxSelectMultiple
    )
    buying_entity = django_filters.MultipleChoiceFilter(
        choices=get_buying_entities_choices(), widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Purchase
        fields = ["purchase_category", "buying_entity"]
