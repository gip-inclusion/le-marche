import django_filters

from lemarche.siaes.models import Siae


class SiaeFilter(django_filters.FilterSet):
    """
    Filtres pour liste SIAE

    Kind : Filtre par choix multiple des types de structure
    Department: Filtrer par numéro du département
    """

    kind = django_filters.MultipleChoiceFilter(label="Type(s) de structure")

    # NOTE: Not all departements are pure numbers
    department = django_filters.CharFilter(label="Numéro du département")

    updated_at = django_filters.IsoDateTimeFromToRangeFilter(label="Date de dernière mise à jour")

    class Meta:
        model = Siae
        fields = ["kind", "department", "updated_at"]
