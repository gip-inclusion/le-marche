from django.http import Http404

from rest_framework import mixins, viewsets
from rest_framework.response import Response

from lemarche.api.sectors.serializers import (
    # SectorSerializer,
    SectorStringSerializer,
)
from lemarche.api.utils import decode_hashed_pk
from lemarche.cocorico.models import SectorString


class SectorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    queryset = SectorString.objects.get_all_active_sectors()
    serializer_class = SectorStringSerializer

    def get_serializer_context(self):
        context = {"hashed_pk": True}
        return context

    def get_object(self, pk):
        try:
            return SectorString.objects.get_sector(pk=pk)
        except SectorString.DoesNotExist:
            raise Http404

    @decode_hashed_pk
    def retrieve(self, request, pk=None, format=None):
        # We override this method to provide the hashed/unhashed PK retrieval
        queryset = self.get_object(pk=pk)
        serializer = SectorStringSerializer(queryset, many=False, context={"hashed_pk": True})
        return Response(serializer.data)
