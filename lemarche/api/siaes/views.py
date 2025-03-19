from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from lemarche.api.siaes.filters import SiaeFilter
from lemarche.api.siaes.serializers import SiaeDetailSerializer
from lemarche.api.utils import BasicChoiceSerializer, BasicChoiceWithParentSerializer
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae


class SiaeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Données d'une structure d'insertion par l'activité économique (SIAE).
    """

    queryset = Siae.objects.api_query_set()
    serializer_class = SiaeDetailSerializer
    filterset_class = SiaeFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "activities", "activities__sectors", "networks", "offers", "client_references", "labels_old"
            )
        )

    @extend_schema(
        summary="Lister toutes les structures",
        tags=[Siae._meta.verbose_name_plural],
    )
    def list(self, request, format=None):
        """
        Liste exhaustive des structures d'insertion par l'activité économique (SIAE).

        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        return super().list(request, format)

    @extend_schema(
        summary="Détail d'une structure (par son id)",
        tags=[Siae._meta.verbose_name_plural],
        responses=SiaeDetailSerializer,
    )
    def retrieve(self, request, pk=None, format=None):
        """
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        return super().retrieve(request, pk, format)

    @extend_schema(
        summary="Détail d'une structure (par son slug)",
        tags=[Siae._meta.verbose_name_plural],
        responses=SiaeDetailSerializer,
    )
    def retrieve_by_slug(self, request, slug=None, format=None):
        """
        Note : le slug est un champ unique.<br /><br />
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        queryset_or_404 = get_object_or_404(self.get_queryset(), slug=slug)
        return self._retrieve_return(request, queryset_or_404, format)

    @extend_schema(
        summary="Détail d'une structure (par son siren)",
        tags=[Siae._meta.verbose_name_plural],
        responses=SiaeDetailSerializer,
    )
    def retrieve_by_siren(self, request, siren=None, format=None):
        """
        Note : le siren n'est pas nécessairement unique, il peut y avoir plusieurs structures retournées.<br /><br />
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        if len(siren) != 9:
            return HttpResponseBadRequest("siren must be 9 caracters long")
        queryset = self.get_queryset().filter(siret__startswith=siren)
        return self._list_return(request, queryset, format)

    @extend_schema(
        summary="Détail d'une structure (par son siret)",
        tags=[Siae._meta.verbose_name_plural],
        responses=SiaeDetailSerializer,
    )
    def retrieve_by_siret(self, request, siret=None, format=None):
        """
        Note : le siret n'est pas nécessairement unique, il peut y avoir plusieurs structures retournées.<br /><br />
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        if len(siret) != 14:
            return HttpResponseBadRequest("siret must be 14 caracters long")
        queryset = self.get_queryset().filter(siret=siret)
        return self._list_return(request, queryset, format)

    def _retrieve_return(self, request, queryset, format):
        serializer = SiaeDetailSerializer(
            queryset,
            many=False,
        )
        return Response(serializer.data)

    def _list_return(self, request, queryset, format):
        serializer = SiaeDetailSerializer(
            queryset,
            many=True,
        )
        return Response(serializer.data)


class SiaeKindViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BasicChoiceWithParentSerializer
    queryset = Siae.objects.none()

    def get_queryset(self):
        siae_kind_insertion = [
            {"id": id, "name": name, "parent": siae_constants.KIND_PARENT_INSERTION_NAME}
            for (id, name) in siae_constants.KIND_INSERTION_CHOICES
        ]
        siae_kind_handicap = [
            {"id": id, "name": name, "parent": siae_constants.KIND_PARENT_HANDICAP_NAME}
            for (id, name) in siae_constants.KIND_HANDICAP_CHOICES
        ]
        siae_kinds = siae_kind_insertion + siae_kind_handicap
        return siae_kinds

    @extend_schema(summary="Lister tous les types de structures", tags=[Siae._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)


class SiaePrestaTypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BasicChoiceSerializer
    queryset = Siae.objects.none()

    def get_queryset(self):
        siae_kinds = [{"id": id, "name": name} for (id, name) in siae_constants.PRESTA_CHOICES]
        return siae_kinds

    @extend_schema(summary="Lister tous les types de prestations", tags=[Siae._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
