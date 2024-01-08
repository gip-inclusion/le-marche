from lemarche.conversations.models import Conversation
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Command to delete outdated conversations

    Note: run via a CRON every day
    Usage: python manage.py delete_outdated_conversations
    """

    def handle(self, *args, **options):
        self.stdout_info("Delete script of outdated conversations")
        conversations_outdated = Conversation.objects.outdated_conversations()
        deleted_count, _ = conversations_outdated.delete()
        self.stdout_info(f"Deleted {deleted_count} outdated conversation(s)")
