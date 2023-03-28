from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from lemarche.api.siaes.filters import SiaeFilter
from lemarche.api.siaes.serializers import SiaeDetailSerializer, SiaeListSerializer
from lemarche.api.utils import BasicChoiceSerializer, check_user_token
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae


class SiaeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Données d'une structure d'insertion par l'activité économique (SIAE).
    """

    queryset = Siae.objects.prefetch_many_to_many()
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
        Liste exhaustive des structures d'insertion par l'activité économique (SIAE).

        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
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
                check_user_token(token)
                return super().list(request, format)

    @extend_schema(
        summary="Détail d'une structure (par son id)",
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeDetailSerializer,
    )
    def retrieve(self, request, pk=None, format=None):
        """
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        queryset = self.get_queryset().prefetch_many_to_one()
        queryset_or_404 = get_object_or_404(queryset, pk=pk)
        return self._retrieve_return(request, queryset_or_404, format)

    @extend_schema(
        summary="Détail d'une structure (par son slug)",
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeDetailSerializer,
    )
    def retrieve_by_slug(self, request, slug=None, format=None):
        """
        Note : le slug est un champ unique.<br /><br />
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        queryset = self.get_queryset().prefetch_many_to_one()
        queryset_or_404 = get_object_or_404(queryset, slug=slug)
        return self._retrieve_return(request, queryset_or_404, format)

    @extend_schema(
        summary="Détail d'une structure (par son siret)",
        tags=[Siae._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=False, type=str),
        ],
        responses=SiaeDetailSerializer,
    )
    def retrieve_by_siret(self, request, siret=None, format=None):
        """
        Note : le siret n'est pas nécessairement unique, il peut y avoir plusieurs structures retournées.<br /><br />
        <i>Un <strong>token</strong> est nécessaire pour l'accès complet à cette ressource.</i>
        """
        queryset = self.get_queryset().prefetch_many_to_one().filter(siret=siret)
        queryset_count = queryset.count()
        if queryset_count == 0:
            raise Http404
        elif queryset_count == 1:
            return self._retrieve_return(request, queryset.first(), format)
        else:
            return self._list_return(request, queryset, format)

    def _retrieve_return(self, request, queryset, format):
        token = request.GET.get("token", None)
        if not token:
            serializer = SiaeListSerializer(
                queryset,
                many=False,
            )
        else:
            check_user_token(token)
            serializer = SiaeDetailSerializer(
                queryset,
                many=False,
            )
        return Response(serializer.data)

    def _list_return(self, request, queryset, format):
        token = request.GET.get("token", None)
        if not token:
            serializer = SiaeListSerializer(
                queryset,
                many=True,
            )
        else:
            check_user_token(token)
            serializer = SiaeDetailSerializer(
                queryset,
                many=True,
            )
        return Response(serializer.data)


class SiaeKindViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BasicChoiceSerializer
    queryset = Siae.objects.none()

    def get_queryset(self):
        siae_kinds = [{"id": id, "name": name} for (id, name) in siae_constants.KIND_CHOICES]
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
