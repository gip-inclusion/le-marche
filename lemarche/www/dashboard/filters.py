import django_filters

from lemarche.purchases.models import Purchase


class PurchaseFilterSet(django_filters.FilterSet):
    inclusive_sector_type = ...
    siae_type = ...

    class Meta:
        model = Purchase
        fields = ["purchase_category", "buying_entity"]
