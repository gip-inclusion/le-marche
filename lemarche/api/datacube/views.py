from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.utils import extend_schema
from rest_framework import authentication, exceptions, generics, permissions

from lemarche.tenders.models import Tender

from .serializers import SimpleTenderSerializer


class DatacubeApiAnonymousUser(AnonymousUser):
    pass


class DatacubeApiAuthentication(authentication.TokenAuthentication):
    def authenticate_credentials(self, key):
        configured_token = settings.DATACUBE_API_TOKEN
        if configured_token and key == configured_token:
            return (DatacubeApiAnonymousUser(), key)
        raise exceptions.AuthenticationFailed("Invalid token.")


class HasTokenOrIsSuperadmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, DatacubeApiAnonymousUser):
            return True
        return request.user.is_superuser


class SimpleTenderList(generics.ListAPIView):
    """Simplified list of tenders along with their listed companies.

    curl -H "Authorization: Token xxxxx" http://marche.fqdn/api/datacube-tenders/
    """

    queryset = (
        Tender.objects.filter(
            created_at__gte=settings.DATACUBE_API_TENDER_START_DATE,
        )
        .exclude(author__isnull=True)
        .prefetch_related("author", "author__company")
        .order_by("-created_at")
        .all()
    )
    serializer_class = SimpleTenderSerializer
    permission_classes = []
    authentication_classes = []

    authentication_classes = (
        DatacubeApiAuthentication,
        authentication.SessionAuthentication,
    )
    permission_classes = (HasTokenOrIsSuperadmin,)

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)
