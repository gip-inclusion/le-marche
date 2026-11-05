import django_filters
from django import forms
from django.db.models import TextChoices

from lemarche.purchases.models import Purchase
from lemarche.siaes.constants import KIND_CHOICES_WITH_EXTRA, KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.utils.widgets import CustomSelectMultiple


def get_distinct_choices(queryset, field_name):
    values = queryset.values_list(field_name, flat=True).order_by(field_name).distinct()
    return [(value, value) for value in values]


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
    # choices are set in __init__, from the (company-scoped) queryset
    purchase_category = django_filters.MultipleChoiceFilter(choices=[], widget=CustomSelectMultiple())
    buying_entity = django_filters.MultipleChoiceFilter(choices=[], widget=CustomSelectMultiple())
    is_qpv = django_filters.BooleanFilter(
        label="Uniquement structures QPV",
        widget=forms.CheckboxInput(),
        method="filter_is_qpv",
    )
    is_zrr = django_filters.BooleanFilter(
        label="Uniquement structures ZRR",
        widget=forms.CheckboxInput(),
        method="filter_is_zrr",
    )

    class Meta:
        model = Purchase
        fields = [
            "inclusive_sector_type",
            "siae_type",
            "purchase_category",
            "buying_entity",
            "is_qpv",
            "is_zrr",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # only expose the values of the purchases the user has access to
        for field_name in ["purchase_category", "buying_entity"]:
            self.filters[field_name].extra["choices"] = get_distinct_choices(self.queryset, field_name)

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

    def filter_is_qpv(self, queryset, name, value):
        if value is True:
            queryset = queryset.filter(siae__isnull=False, siae__is_qpv=True)
        return queryset

    def filter_is_zrr(self, queryset, name, value):
        if value is True:
            queryset = queryset.filter(siae__isnull=False, siae__is_zrr=True)
        return queryset
