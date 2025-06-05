from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Import new buyers from a csv file."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--brevo-template_id",
            type=int,
            help="ID de la template de mail Brevo pour envoyer l'invitation aux acheteurs importés.",
        )
        parser.add_argument(
            "--brevo-contact_id",
            type=int,
            help="ID de la liste de contact Brevo à utiliser pour les acheteurs importés.",
        )

    def handle(self, *args, **options):
        pass
