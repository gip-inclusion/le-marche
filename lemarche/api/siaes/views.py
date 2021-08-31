from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from hashids import Hashids
from rest_framework import generics, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from lemarche.api.siaes.serializers import (
    # SectorSerializer,
    SectorStringSerializer,
    # SiaeHyperSerializer,
    SiaeSerializer,
    SiaeAnonSerializer,
    SiaeListSerializer,
    SiaeListAnonSerializer,
)
from lemarche.api.siaes.filters import SiaeFilter
from lemarche.cocorico.models import Directory, DirectorySector, Sector, SectorString
from lemarche.users.models import User


hasher = Hashids(alphabet="1234567890ABCDEF", min_length=5)

"""
Inspiration for class-based views :
    https://www.django-rest-framework.org/tutorial/3-class-based-views/
Generic viewset:
    https://www.django-rest-framework.org/api-guide/viewsets/#genericviewset
"""


# ################################################################## FUNCTIONS
# ############################################################################
# TODO: create common shared lib for reusable components

# Custom Service Exceptions
class Unauthorized(APIException):
    status_code = 401
    default_detail = "Unauthorized"
    default_code = "unauthorized"


def decode_hashed_pk(func):
    """
    Small decorator to dynamically decode a hashed pk
    """

    def _wrapper(*args, **kwargs):
        if "pk" in kwargs.keys():
            kwargs["pk"] = hasher.decode(kwargs["pk"])[0]
        return func(*args, **kwargs)

    return _wrapper


def ensure_user_permission(token):
    """
    User token functionnality is temporary, and only used
    to trace API usage and support : once a proper
    auth protocol is implemented it is to be replaced
    """
    try:
        user = User.objects.get(api_key=token)
        assert user.has_perm("api.access_api")
    except (User.DoesNotExist, AssertionError):
        raise Unauthorized


# ###################################################################### VIEWS
# ############################################################################


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
