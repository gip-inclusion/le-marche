from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from lemarche.api.siaes.filters import SiaeFilter
from lemarche.api.siaes.serializers import SiaeAnonSerializer, SiaeChoiceSerializer, SiaeListSerializer, SiaeSerializer
from lemarche.api.utils import ensure_user_permission
from lemarche.siaes.models import Siae


class SiaeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Données d'une structure d'insertion par l'activité économique (SIAE).
    """

    # ModelViewSet needs 'queryset' to be set otherwise the router won't be
    # able to derive the model Basename. To avoid loading data on object
    # initialisation we load an empty queryset.
    queryset = Siae.objects.prefetch_related("sectors", "networks").all()
    serializer_class = SiaeListSerializer
    filter_class = SiaeFilter

    @extend_schema(
        summary="Lister toutes les structures",
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
    )
    def list(self, request, format=None):
        """
        Liste exhaustive des structures d'insertion par l'activité économique (SIAE)

        Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.
        """
        if request.method == "GET":
            token = request.GET.get("token", None)
            if not token:
                serializer = SiaeListSerializer(
                    Siae.objects.all()[:10],
                    many=True,
                )
                return Response(serializer.data)
            else:
                ensure_user_permission(token)
                return super().list(request, format)

    @extend_schema(
        summary="Détail d'une structure (par son id)",
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeSerializer,
    )
    def retrieve(self, request, pk=None, format=None):
        """
        Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.
        """
        queryset = get_object_or_404(self.get_queryset(), pk=pk)
        return self._retrieve_return(request, queryset, format)

    @extend_schema(
        summary="Détail d'une structure (par son siret)",
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeSerializer,
    )
    def retrieve_by_siret(self, request, siret=None, format=None):
        """
        Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.
        """
        queryset = get_object_or_404(self.get_queryset(), siret=siret)
        return self._retrieve_return(request, queryset, format)

    def _retrieve_return(self, request, queryset, format):
        token = request.GET.get("token", None)
        if not token:
            serializer = SiaeAnonSerializer(
                queryset,
                many=False,
            )
        else:
            ensure_user_permission(token)
            serializer = SiaeSerializer(
                queryset,
                many=False,
            )

        return Response(serializer.data)


class SiaeKindViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SiaeChoiceSerializer
    queryset = Siae.objects.none()

    def get_queryset(self):
        siae_kinds = [{"id": id, "name": name} for (id, name) in Siae.KIND_CHOICES]
        return siae_kinds

    @extend_schema(summary="Lister tous les types de structures", tags=[Siae._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)


class SiaePrestaTypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SiaeChoiceSerializer
    queryset = Siae.objects.none()

    def get_queryset(self):
        siae_kinds = [{"id": id, "name": name} for (id, name) in Siae.PRESTA_CHOICES]
        return siae_kinds

    @extend_schema(summary="Lister tous les types de prestations", tags=[Siae._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
