from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone

from lemarche.conversations.models import Conversation
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Command to anonymize outdated conversations

    Note: run via a CRON every day
    Usage: python manage.py anonymize_outdated_conversations
    """

    def handle(self, *args, **options):
        inactive_datetime = timezone.now() - relativedelta(months=settings.INACTIVE_CONVERSATION_TIMEOUT_IN_MONTHS)
        outdated_conversations = Conversation.objects.filter(created_at__lte=inactive_datetime, is_anonymized=False)

        for conversation in outdated_conversations:
            conversation.sender_user = None
            conversation.sender_email = None
            conversation.sender_first_name = ""
            conversation.sender_last_name = ""
            conversation.initial_body_message = str(len(conversation.initial_body_message))
            conversation.data = [str(len(conversation.data))]
            conversation.is_anonymized = True

        Conversation.objects.bulk_update(
            outdated_conversations,
            fields=[
                "sender_user",
                "sender_email",
                "sender_first_name",
                "sender_last_name",
                "initial_body_message",
                "data",
                "is_anonymized",
            ],
        )
