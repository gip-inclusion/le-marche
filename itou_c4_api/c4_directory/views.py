from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from c4_directory.models import Siae
from c4_directory.serializers import SiaeSerializer

@csrf_exempt
def siae_list(request):
    if request.method == 'GET':
        siaes = Siae.objects.all()
        serializer = SiaeSerializer(siaes, many=True)
        return JsonResponse(serializer.data, safe=False)
