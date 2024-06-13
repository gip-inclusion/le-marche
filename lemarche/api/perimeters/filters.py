import django_filters
from django.conf import settings

from lemarche.perimeters.models import Perimeter


class PerimeterFilter(django_filters.FilterSet):
    kind = django_filters.MultipleChoiceFilter(label="Type(s) de périmètre", choices=Perimeter.KIND_CHOICES)

    class Meta:
        model = Perimeter
        fields = ["kind"]


class PerimeterAutocompleteFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        label="Nom ou code postal du périmètre. Fragment de nom ou de code postal possible : lyon, gre, aix, 38100, 7500, 01…",  # noqa
        method="name_or_post_code_autocomplete_search",
        required=True,
    )
    results = django_filters.NumberFilter(
        label=f"Nombre maximum de résultats (choisir un chiffre inférieur à {settings.API_PERIMETER_AUTOCOMPLETE_MAX_RESULTS})",  # noqa
        method="max_number_of_results",
    )

    class Meta:
        model = Perimeter
        fields = ["q", "results"]

    def name_or_post_code_autocomplete_search(self, queryset, name, value):
        return queryset.name_or_post_code_autocomplete_search(value)

    def max_number_of_results(self, queryset, name, value):
        if not value:
            return queryset
        return queryset[:value]
