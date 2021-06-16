# from lemarche.api.models import Siae
from lemarche.api.siaes.serializers import (
    # SectorSerializer,
    SectorStringSerializer,
    # SiaeHyperSerializer,
    SiaeLightSerializer,
    SiaeSerializer,
)
from lemarche.cocorico.models import Directory, DirectorySector, Sector, SectorString
from lemarche.users.models import User
from django.http import HttpResponse
from django.http import Http404
from hashids import Hashids
from rest_framework import generics, mixins
from rest_framework.views import APIView
from rest_framework.response import Response


hasher = Hashids(alphabet="1234567890ABCDEF", min_length=5)

"""
Inspiration for class-based views :
    https://www.django-rest-framework.org/tutorial/3-class-based-views/
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


#  FIXME:Given the peculiar user-token access, it's not possible
# to use generic class-based views at this moment.
class SiaeList(APIView):
    """
    Lister les SIAES
    """

    def get(self, request, format=None):
        if request.method == "GET":
            siaes = Directory.objects.all()
            token = request.GET.get("token", None)
            if not token:
                # serializer = SiaeLightSerializer(siaes[:10], many=True)
                serializer = SiaeLightSerializer(
                    siaes[:10],
                    many=True,
                    context={"hashed_pk": True},
                )
            else:

                try:
                    user = User.objects.get(api_key=token)
                    assert user.has_perm("api.access_api")
                except User.DoesNotExist:
                    return HttpResponse("503: Not Allowed", status=503)

                serializer = SiaeLightSerializer(
                    siaes,
                    many=True,
                    context={"hashed_pk": True},
                )
            # return JsonResponse(serializer.data, safe=False)
            return Response(serializer.data)


# FIXME: Given the peculiar user-token access, it's not possible
# to use generic class-based views at this moment.
class SiaeDetail(APIView):
    """
    Lecture des SIAES
    """

    def get_object(self, pk):
        try:
            return Directory.objects.get(pk=pk)
        except Directory.DoesNotExist:
            raise Http404

    @decode_hashed_pk
    def get(self, request, pk, format=None):
        """
        Détail d'une structure
        """
        siae = self.get_object(pk)
        token = request.GET.get("token", None)
        if not token:
            serializer = SiaeLightSerializer(
                siae,
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
                siae,
                many=False,
                context={"hashed_pk": True},
            )
        return Response(serializer.data)


class SectorList(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = SectorString.objects.get_all_active_sectors()
    serializer_class = SectorStringSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = {"hashed_pk": True}
        return context


class SectorDetail(APIView):
    def get_object(self, pk):
        try:
            return SectorString.objects.get_sector(pk=pk)
        except SectorString.DoesNotExist:
            raise Http404

    @decode_hashed_pk
    def get(self, request, pk, format=None):
        sector = self.get_object(pk)
        serializer = SectorStringSerializer(sector, many=False, context={"hashed_pk": True})
        return Response(serializer.data)
