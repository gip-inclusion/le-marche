from rest_framework import mixins, viewsets
from drf_spectacular.utils import extend_schema

from lemarche.sectors.models import Sector
from lemarche.api.sectors.serializers import SectorSerializer


class SectorViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer

    @extend_schema(tags=[Sector._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
