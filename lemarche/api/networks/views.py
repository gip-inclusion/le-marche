from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets

from lemarche.api.networks.serializers import NetworkSerializer
from lemarche.networks.models import Network


class NetworkViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer

    @extend_schema(summary="Lister tous les réseaux", tags=[Network._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
