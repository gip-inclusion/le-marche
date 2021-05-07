from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from c4_directory.models import Siae
from c4_directory.serializers import SiaeSerializer

@csrf_exempt
@api_view(['GET'])
def siae_list(request):
    if request.method == 'GET':
        siaes = Siae.objects.all()
        serializer = SiaeSerializer(siaes, many=True)
        # return JsonResponse(serializer.data, safe=False)
        return Response(serializer.data)
