import django_filters
from django.db.models import TextChoices

from lemarche.purchases.models import Purchase
from lemarche.siaes.constants import KIND_CHOICES_WITH_EXTRA, KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.utils.widgets import CustomSelectMultiple


def get_purchase_category_choices():
    purchase_categories = (
        Purchase.objects.values_list("purchase_category", flat=True).order_by("purchase_category").distinct()
    )
    return [(purchase_category, purchase_category) for purchase_category in purchase_categories]


def get_buying_entities_choices():
    buying_entities = Purchase.objects.values_list("buying_entity", flat=True).order_by("buying_entity").distinct()
    return [(buying_entity, buying_entity) for buying_entity in buying_entities]


class PurchaseFilterSet(django_filters.FilterSet):
    class InclusiveSectorTypeChoices(TextChoices):
        INSERTION = "INSERTION", "Insertion"
        HANDICAP = "HANDICAP", "Handicap"

    inclusive_sector_type = django_filters.MultipleChoiceFilter(
        label="Type de secteur inclusif",
        widget=CustomSelectMultiple(),
        method="filter_inclusive_sector_type",
        choices=InclusiveSectorTypeChoices.choices,
    )
    siae_type = django_filters.MultipleChoiceFilter(
        label="Type de structure",
        widget=CustomSelectMultiple(),
        method="filter_siae_type",
        choices=KIND_CHOICES_WITH_EXTRA,
    )
    purchase_category = django_filters.MultipleChoiceFilter(
        choices=get_purchase_category_choices, widget=CustomSelectMultiple()
    )
    buying_entity = django_filters.MultipleChoiceFilter(
        choices=get_buying_entities_choices, widget=CustomSelectMultiple()
    )

    class Meta:
        model = Purchase
        fields = ["inclusive_sector_type", "siae_type", "purchase_category", "buying_entity"]

    def filter_inclusive_sector_type(self, queryset, name, value):
        kind_list = []
        if self.InclusiveSectorTypeChoices.INSERTION in value:
            kind_list.extend(KIND_INSERTION_LIST)
        if self.InclusiveSectorTypeChoices.HANDICAP in value:
            kind_list.extend(KIND_HANDICAP_LIST)

        if kind_list:
            queryset = queryset.filter(siae__kind__in=kind_list)

        return queryset

    def filter_siae_type(self, queryset, name, value):
        return queryset.filter(siae__kind__in=value)
