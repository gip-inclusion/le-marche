import django_filters
from django.contrib.postgres.search import TrigramSimilarity

from lemarche.perimeters.models import Perimeter


class PerimeterFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        label="Nom du périmètre. Fragment de nom possible : lyon, gre, aix…", method="name_autocomplete_search"
    )
    kind = django_filters.MultipleChoiceFilter(label="Type(s) de périmètre", choices=Perimeter.KIND_CHOICES)
    results = django_filters.NumberFilter(label="Nombre maximum de résultats", method="max_number_of_results")

    class Meta:
        model = Perimeter
        fields = ["name", "kind", "results"]

    def name_autocomplete_search(self, queryset, name, value):
        if not value:
            return queryset
        return (
            queryset.annotate(similarity=TrigramSimilarity("name", value))
            .filter(similarity__gt=0.1)
            .order_by("-similarity")
        )

    def max_number_of_results(self, queryset, name, value):
        if not value:
            return queryset
        return queryset[:value]
