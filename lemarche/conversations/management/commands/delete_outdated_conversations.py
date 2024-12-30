from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Command to delete outdated conversations

    Note: run via a CRON every day
    Usage: python manage.py delete_outdated_conversations
    """

    def handle(self, *args, **options):
        pass
