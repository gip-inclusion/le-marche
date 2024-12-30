from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Command to anonymize outdated conversations

    Note: run via a CRON every day
    Usage: python manage.py anonymize_outdated_conversations
    """

    def handle(self, *args, **options):
        pass
