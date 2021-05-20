from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from c4_directory.models import Siae
from c4_directory.serializers import  (
    SiaeSerializer,
    SectorSerializer,
    SectorStringSerializer,
)
from cocorico.models import (
    Directory,
    Sector,
    SectorString
)

@csrf_exempt
@api_view(['GET'])
def siae_list(request):
    """
    Liste des structures inclusives reprises dans le marché de l'inclusion.
    """
    if request.method == 'GET':
        siaes = Directory.objects.all()
        serializer = SiaeSerializer(siaes, many=True)
        # return JsonResponse(serializer.data, safe=False)
        return Response(serializer.data)

@csrf_exempt
@api_view(['GET'])
def siae_detail(request, key):
    """
    Détail d'une structure
    """
    try:
        siae = Directory.objects.get(pk=key)
        serializer = SiaeSerializer(siae, many=False)
        return Response(serializer.data)
    except Siae.DoesNotExist:
        return HttpResponse(status=404)


@csrf_exempt
@api_view(['GET'])
def sector_list(request):
    """
    Liste hiérarchisée des secteurs d'activité des structures.
    """
    if request.method == 'GET':
        #sectors = Sector.objects.select_related('SectorString').all()
        sectors = SectorString.objects.select_related('translatable').all()
        #sectors = Sector.objects.all()
        serializer = SectorStringSerializer(sectors, many=True)
        return Response(serializer.data)
