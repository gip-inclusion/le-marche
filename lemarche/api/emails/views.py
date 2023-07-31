from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.emails.serializers import EmailsSerializer


class InboundParsingEmailView(APIView):
    def post(self, request):
        serializer = EmailsSerializer(data=request.data)
        if serializer.is_valid():
            # TODO make transfert
            inboundEmail = serializer.validated_data.get("items")[0]
            print("Transfert email from : ", inboundEmail["From"])
            print("To : ", inboundEmail["To"])
            print("Content Email Text : ", inboundEmail["RawTextBody"])
            print("Content Email Html : ", inboundEmail["RawHtmlBody"])
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
