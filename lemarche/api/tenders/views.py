from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets

from lemarche.api.tenders.serializers import TenderSerializer
from lemarche.tenders.models import Tender


class TenderViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = TenderSerializer

    @extend_schema(summary="Déposer un besoin d'achat", tags=[Tender._meta.verbose_name_plural])
    def create(self, request, *args, **kwargs):
        return super().create(request, args, kwargs)
