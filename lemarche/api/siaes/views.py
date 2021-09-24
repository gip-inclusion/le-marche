from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from lemarche.api.siaes.filters import SiaeFilter
from lemarche.api.siaes.serializers import (  # SiaeHyperSerializer,
    SiaeAnonSerializer,
    SiaeListAnonSerializer,
    SiaeListSerializer,
    SiaeSerializer,
)
from lemarche.api.utils import ensure_user_permission
from lemarche.siaes.models import Siae


class SiaeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Données d'une structure d'insertion par l'activité économique (SIAE).
    """

    # ModelViewSet needs 'queryset' to be set otherwise the router won't be
    # able to derive the model Basename. To avoid loading data on object
    # initialisation we load an empty queryset.
    queryset = Siae.objects.all()
    serializer_class = SiaeListSerializer
    filter_class = SiaeFilter

    @extend_schema(
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
    )
    def list(self, request, format=None):
        """
        Liste exhaustive des structures d'insertion par l'activité économique (SIAE).
        """
        if request.method == "GET":

            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            token = request.GET.get("token", None)
            if not token:
                serializer = SiaeListAnonSerializer(
                    queryset[:10],
                    many=True,
                )
            else:
                ensure_user_permission(token)
                serializer = SiaeListSerializer(
                    page,
                    many=True,
                )

            return self.get_paginated_response(serializer.data)

    @extend_schema(
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeSerializer,
    )
    def retrieve(self, request, pk=None, format=None):
        """
        Détail d'une structure
        """
        queryset = get_object_or_404(self.get_queryset(), pk=pk)
        return self._retrieve_return(request, queryset, format)

    @extend_schema(
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeSerializer,
    )
    def retrieve_by_siret(self, request, siret=None, format=None):
        """
        Détail d'une structure
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
