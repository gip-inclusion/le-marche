from django.core.management.base import BaseCommand

from lemarche.conversations.models import Conversation


class Command(BaseCommand):
    """
    Command to send validated tenders

    Note: run via a CRON every day
    Usage: python manage.py delete_outdated_conversations
    """

    def handle(self, *args, **options):
        oudated_conversations = Conversation.objects.oudated_conversations()
        numb_delete, _ = oudated_conversations.delete()
        self.stdout.write(f"Delete {numb_delete} conversation(s)")
