from rest_framework import mixins, viewsets
from drf_spectacular.utils import extend_schema

from lemarche.networks.models import Network
from lemarche.api.networks.serializers import NetworkSerializer


class NetworkViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer

    @extend_schema(tags=[Network._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
