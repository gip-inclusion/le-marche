import django_filters

from lemarche.networks.models import Network
from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae


class SiaeFilter(django_filters.FilterSet):
    kind = django_filters.MultipleChoiceFilter(label="Type(s) de structure", choices=siae_constants.KIND_CHOICES)
    presta_type = django_filters.MultipleChoiceFilter(
        label="Type(s) de prestation", choices=siae_constants.PRESTA_CHOICES, lookup_expr="icontains"
    )
    department = django_filters.CharFilter(label="Numéro du département")
    sectors = django_filters.ModelMultipleChoiceFilter(
        label="Secteur(s) d'activité<br /><br /><i>Mettre le slug de chaque secteur d'activité</i>",
        field_name="sectors__slug",
        to_field_name="slug",
        queryset=Sector.objects.all(),
    )
    networks = django_filters.ModelMultipleChoiceFilter(
        label="Réseau(x)<br /><br /><i>Mettre le slug de chaque réseau</i>",
        field_name="networks__slug",
        to_field_name="slug",
        queryset=Network.objects.all(),
    )
    is_active = django_filters.BooleanFilter(label="Convention active (ASP) ou import")
    updated_at = django_filters.IsoDateTimeFromToRangeFilter(label="Date de dernière mise à jour")

    class Meta:
        model = Siae
        fields = ["kind", "presta_type", "department", "is_active", "updated_at"]
