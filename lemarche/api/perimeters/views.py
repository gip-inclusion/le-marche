from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets

from lemarche.api.perimeters.filters import PerimeterFilter
from lemarche.api.perimeters.serializers import PerimeterChoiceSerializer, PerimeterSimpleSerializer
from lemarche.perimeters.models import Perimeter


class PerimeterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Perimeter.objects.all()
    serializer_class = PerimeterSimpleSerializer
    filter_class = PerimeterFilter

    @extend_schema(tags=[Perimeter._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)


class PerimeterKindViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PerimeterChoiceSerializer
    queryset = Perimeter.objects.none()

    def get_queryset(self):
        siae_kinds = [{"id": id, "name": name} for (id, name) in Perimeter.KIND_CHOICES]
        return siae_kinds

    @extend_schema(summary="Lister tous les choix de types de périmètres", tags=[Perimeter._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
