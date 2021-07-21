import django_filters
from lemarche.api.models import Siae
from lemarche.cocorico.models import Directory

TYPE_CHOICES = (
    ("EI", "EI"),
    ("EA", "EA"),
    ("EITI", "EITI"),
    ("ETTI", "ETTI"),
    ("EATT", "EATT"),
    ("ACI", "ACI"),
    ("AI", "AI"),
    ("GEIQ", "GEIQ"),
)


class SiaeFilter(django_filters.FilterSet):
    """
    Filtres pour liste SIAE

    Type : Filtre par choix multiple des types de structure
    Departement: Filtrer par numéro du département
    """

    type = django_filters.MultipleChoiceFilter(field_name="kind", label="Type(s) de structure", choices=TYPE_CHOICES)
    updatedat = django_filters.IsoDateTimeFromToRangeFilter(label="Date de dernière mise à jour")

    # NOTE: Not all departements are pure numbers
    departement = django_filters.CharFilter(
        label="Numéro du département",
        field_name="department",
    )

    class Meta:
        model = Directory
        fields = ["type", "departement", "updatedat"]
