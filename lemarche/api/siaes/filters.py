import django_filters

from lemarche.siaes.models import Siae


class SiaeFilter(django_filters.FilterSet):
    """
    Filtres pour liste SIAE

    kind : Filtre par choix multiple des types de structures
    presta_type : Filtre par choix multiple des types de prestations
    department: Filtrer par numéro du département
    """

    kind = django_filters.MultipleChoiceFilter(label="Type(s) de structure")
    presta_type = django_filters.MultipleChoiceFilter(
        label="Type(s) de prestation", choices=Siae.PRESTA_CHOICES, lookup_expr="icontains"
    )

    # NOTE: Not all departements are pure numbers
    department = django_filters.CharFilter(label="Numéro du département")

    updated_at = django_filters.IsoDateTimeFromToRangeFilter(label="Date de dernière mise à jour")

    class Meta:
        model = Siae
        fields = ["kind", "presta_type", "department", "updated_at"]
