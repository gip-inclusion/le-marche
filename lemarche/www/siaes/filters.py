from django_filters import CharFilter, FilterSet

from lemarche.siaes.models import Siae


class SiaeSiretFilterForm(FilterSet):
    siret = CharFilter(lookup_expr="exact", label="Indiquez votre SIRET", max_length=14, min_length=14)

    class Meta:
        model = Siae
        fields = ["siret"]
