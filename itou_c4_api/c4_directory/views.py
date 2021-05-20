from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from c4_directory.models import Siae
from c4_directory.serializers import  (
    SiaeSerializer,
    SectorSerializer,
)
from cocorico.models import (
    Directory,
    Sector,
    SectorString
)

@csrf_exempt
@api_view(['GET'])
def siae_list(request):
    if request.method == 'GET':
        siaes = Directory.objects.all()
        serializer = SiaeSerializer(siaes, many=True)
        # return JsonResponse(serializer.data, safe=False)
        return Response(serializer.data)

@csrf_exempt
@api_view(['GET'])
def siae_detail(request, key):
    try:
        siae = Directory.objects.get(pk=key)
        serializer = SiaeSerializer(siae, many=False)
        return Response(serializer.data)
    except Siae.DoesNotExist:
        return HttpResponse(status=404)


@csrf_exempt
@api_view(['GET'])
def sector_list(request):
    if request.method == 'GET':
        #sectors = ListingCategory.select_related('ListingCategoryTranslation').objects.all()
        sectors = Sector.objects.all()
        serializer = SectorSerializer(sectors, many=True)
        return Response(serializer.data)
