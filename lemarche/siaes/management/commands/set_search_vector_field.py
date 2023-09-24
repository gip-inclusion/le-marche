from django.contrib.postgres.search import SearchVector

from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Usage:
    - poetry run python manage.py set_search_vector_field
    """

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Reseting search_vector field...")
        for siae in Siae.objects.all():
            siae_search_vector = (
                SearchVector(
                    "offers__name",
                    # weight="A",
                    config="french",
                )
                + SearchVector(
                    "description",
                    # weight="A",
                    config="french",
                )
                + SearchVector(
                    "labels__name",
                    # weight="A",
                    config="french",
                )
            )
            Siae.objects.filter(id=siae.id).update(search_vector=siae_search_vector)
