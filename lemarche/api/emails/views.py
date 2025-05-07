import ipaddress
import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.emails.serializers import EmailsSerializer
from lemarche.conversations.constants import ATTRIBUTES_TO_SAVE_FOR_INBOUND
from lemarche.conversations.models import Conversation
from lemarche.conversations.utils import get_info_from_email_prefix
from lemarche.www.conversations.tasks import send_email_from_conversation


logger = logging.getLogger(__name__)


def clean_saved_data_of_inbound(data_inbound: dict):
    """We clean saved data to respect the law of RGPD

    Args:
        data_inbound (dict): all data that we receive from inbound api

    Returns:
        dict with only neccessary key to save
    """
    clean_saved_data = {}
    for key in ATTRIBUTES_TO_SAVE_FOR_INBOUND:
        clean_saved_data[key] = data_inbound.get(key)
    return clean_saved_data


class BrevoWhitelistPermission(BasePermission):
    """
    Permission check for allowed IPs.
    """

    def has_permission(self, request, view) -> bool:
        """Check if ip adress is in network range"""
        ip_addr = ipaddress.ip_address(request.META["REMOTE_ADDR"])
        network = ipaddress.ip_network(settings.BREVO_IP_WHITELIST_RANGE)

        has_permission = ip_addr in network
        if has_permission:
            logger.info("BrevoWhitelistPermission: %s has permission", ip_addr)
        else:
            logger.warning("BrevoWhitelistPermission: %s has no permission", ip_addr)
        return has_permission


class InboundParsingEmailView(APIView):
    permission_classes = [BrevoWhitelistPermission]  # override the default class that requires Authentication

    @extend_schema(exclude=True)
    def post(self, request):
        serializer = EmailsSerializer(data=request.data)
        remote_addr = ipaddress.ip_address(request.META["REMOTE_ADDR"])
        logger.info("InboundParsingEmailView called from %s", remote_addr)
        if serializer.is_valid():
            inbound_email = serializer.validated_data.get("items")[0]
            inbound_email_prefix = inbound_email["To"][0]["Address"].split("@")[0]
            # get conversation object
            version, conv_uuid, user_kind = get_info_from_email_prefix(inbound_email_prefix)
            conv: Conversation = Conversation.objects.get_conv_from_uuid(conv_uuid=conv_uuid, version=version)
            # save the input data
            data_inbound_clean = clean_saved_data_of_inbound(data_inbound=serializer.data.get("items")[0])
            conv.data.append(data_inbound_clean)
            conv.save()
            logger.info("InboundParsingEmailView saved data for conversation %s", conv.uuid)
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
            logger.error("INBOUND_PARSING_WEBHOOK_ERROR : %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
