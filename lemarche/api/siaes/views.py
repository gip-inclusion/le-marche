# from lemarche.api.models import Siae
from lemarche.api.siaes.serializers import (
    # SectorSerializer,
    SectorStringSerializer,
    # SiaeHyperSerializer,
    SiaeSerializer,
    SiaeAnonSerializer,
    SiaeListSerializer,
    SiaeListAnonSerializer,
)
from lemarche.api.siaes.filters import (
    SiaeFilter,
)
from lemarche.cocorico.models import Directory, DirectorySector, Sector, SectorString
from lemarche.users.models import User
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from hashids import Hashids
from rest_framework import generics, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


hasher = Hashids(alphabet="1234567890ABCDEF", min_length=5)

"""
Inspiration for class-based views :
    https://www.django-rest-framework.org/tutorial/3-class-based-views/
Generic viewset:
    https://www.django-rest-framework.org/api-guide/viewsets/#genericviewset
"""


# TODO: create common shared lib for reusable components
def decode_hashed_pk(func):
    """
    Small decorator to dynamically decode a hashed pk
    """

    def _wrapper(*args, **kwargs):
        if "pk" in kwargs.keys():
            kwargs["pk"] = hasher.decode(kwargs["pk"])[0]
        return func(*args, **kwargs)

    return _wrapper


class Siae(mixins.ListModelMixin,
           mixins.RetrieveModelMixin,
           viewsets.GenericViewSet):
    """
    Données d'une structure d'insertion par l'activité économique (SIAE).
    """

    queryset = Directory.objects.all()
    serializer_class = SiaeListSerializer
    filter_class = SiaeFilter

    def get_object_by_id(self, pk):
        try:
            return Directory.objects.get(pk=pk)
        except Directory.DoesNotExist:
            raise Http404

    def get_object_by_siret(self, siret):
        try:
            return Directory.objects.get(siret=siret)
        except Directory.DoesNotExist:
            raise Http404

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='token',
                description='Token Utilisateur',
                required=False,
                type=str),
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
                try:
                    user = User.objects.get(api_key=token)
                    assert user.has_perm("api.access_api")
                except User.DoesNotExist:
                    return HttpResponse("503: Not Allowed", status=503)

                serializer = SiaeListSerializer(
                    page,
                    many=True,
                    context={"hashed_pk": True},
                )

            return self.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='token',
                description='Token Utilisateur',
                required=False,
                type=str),
        ],
        responses=SiaeSerializer,
    )
    @decode_hashed_pk
    def retrieve_by_id(self, request, pk=None, format=None):
        """
        Détail d'une structure
        """
        queryset = self.get_object_by_id(pk=pk)
        token = request.GET.get("token", None)
        if not token:
            serializer = SiaeAnonSerializer(
                queryset,
                many=False,
                context={"hashed_pk": True},
            )
        else:
            try:
                user = User.objects.get(api_key=token)
                assert user.has_perm("api.access_api")
            except User.DoesNotExist:
                return HttpResponse("503: Not Allowed", status=503)

            serializer = SiaeSerializer(
                queryset,
                many=False,
                context={"hashed_pk": True},
            )
        return Response(serializer.data)


    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='token',
                description='Token Utilisateur',
                required=False,
                type=str),
        ],
        responses=SiaeSerializer,
    )
    def retrieve_by_siret(self, request, siret=None, format=None):
        """
        Détail d'une structure
        """
        queryset = self.get_object_by_siret(siret=siret)
        token = request.GET.get("token", None)
        if not token:
            serializer = SiaeAnonSerializer(
                queryset,
                many=False,
                context={"hashed_pk": True},
            )
        else:
            try:
                user = User.objects.get(api_key=token)
                assert user.has_perm("api.access_api")
            except User.DoesNotExist:
                return HttpResponse("503: Not Allowed", status=503)

            serializer = SiaeSerializer(
                queryset,
                many=False,
                context={"hashed_pk": True},
            )
        return Response(serializer.data)


class Sectors(mixins.ListModelMixin,
              mixins.RetrieveModelMixin,
              viewsets.GenericViewSet):

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
        queryset = self.get_object(pk=pk)
        serializer = SectorStringSerializer(queryset, many=False, context={"hashed_pk": True})
        return Response(serializer.data)
