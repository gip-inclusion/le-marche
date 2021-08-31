from django.shortcuts import get_object_or_404

from rest_framework import mixins, viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from lemarche.api.siaes.serializers import (
    # SiaeHyperSerializer,
    SiaeSerializer,
    SiaeAnonSerializer,
    SiaeListSerializer,
    SiaeListAnonSerializer,
)
from lemarche.api.siaes.filters import SiaeFilter
from lemarche.api.utils import ensure_user_permission, decode_hashed_pk
from lemarche.cocorico.models import Directory


class SiaeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Données d'une structure d'insertion par l'activité économique (SIAE).
    """

    # ModelViewSet needs 'queryset' to be set otherwise the router won't be
    # able to derive the model Basename. To avoid loading data on object
    # initialisation we load an empty queryset.
    queryset = Directory.objects.all()
    serializer_class = SiaeListSerializer
    filter_class = SiaeFilter

    @extend_schema(
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ]
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
                    context={"hashed_pk": True},
                )
            else:
                ensure_user_permission(token)
                serializer = SiaeListSerializer(
                    page,
                    many=True,
                    context={"hashed_pk": True},
                )

            return self.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeSerializer,
    )
    @decode_hashed_pk
    def retrieve_by_id(self, request, pk=None, format=None):
        """
        Détail d'une structure
        """
        queryset = get_object_or_404(self.get_queryset(), pk=pk)
        return self._retrieve_return(request, queryset, format)

    @extend_schema(
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
                context={"hashed_pk": True},
            )
        else:
            ensure_user_permission(token)
            serializer = SiaeSerializer(
                queryset,
                many=False,
                context={"hashed_pk": True},
            )

        return Response(serializer.data)
