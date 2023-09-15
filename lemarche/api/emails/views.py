import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.emails.serializers import EmailsSerializer
from lemarche.conversations.models import Conversation
from lemarche.conversations.utils import get_info_from_email_prefix
from lemarche.www.conversations.tasks import send_email_from_conversation


logger = logging.getLogger(__name__)


class InboundParsingEmailView(APIView):
    def post(self, request):
        serializer = EmailsSerializer(data=request.data)
        if serializer.is_valid():
            inbound_email = serializer.validated_data.get("items")[0]
            inbound_email_prefix = inbound_email["To"][0]["Address"].split("@")[0]
            # get conversation object
            version, conv_uuid, user_kind = get_info_from_email_prefix(inbound_email_prefix)
            conv: Conversation = Conversation.objects.get_conv_from_uuid(conv_uuid=conv_uuid, version=version)
            # save the input data
            conv.data.append(serializer.data)
            conv.save()
            # find user_kind
            if version >= 1:
                user_kind = conv.get_user_kind(conv_uuid)
            # make the transfer of emails
            send_email_from_conversation(
                conv=conv,
                user_kind=user_kind,
                email_subject=inbound_email.get("Subject", conv.title),
                email_body=inbound_email.get("RawTextBody"),
                email_body_html=inbound_email.get("RawHtmlBody"),
            )
            return Response(conv.uuid, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"[INBOUND_PARSING_WEBHOOK_ERROR] {str(serializer.errors)}")
            logger.error(f"[INBOUND_PARSING_WEBHOOK_ERROR] {str(serializer.data)}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
