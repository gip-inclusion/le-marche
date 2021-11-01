import django_filters
from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

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
        if not value:
            return queryset
        # department code or city post_code
        if value.isnumeric():
            # city post_code
            if len(value) == 5:
                queryset = queryset.filter(post_codes__contains=[value])
                # if we wanted to allow search on insee_code as well
                # return queryset.filter(Q(insee_code=value) | Q(post_codes__contains=[value]))
            # department code or beginning of city post_code
            elif len(value) == 2:
                queryset = queryset.filter(Q(insee_code=value) | Q(post_codes__0__startswith=value))
            # city post_code
            else:
                queryset = queryset.filter(post_codes__0__startswith=value)
            return queryset.order_by("insee_code")
        # normal name filtering
        return (
            queryset.annotate(similarity=TrigramSimilarity("name", value))
            .filter(similarity__gt=0.1)
            .order_by("-similarity")
        )

    def max_number_of_results(self, queryset, name, value):
        if not value:
            return queryset
        return queryset[:value]
