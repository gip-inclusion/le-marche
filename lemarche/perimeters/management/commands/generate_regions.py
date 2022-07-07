import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class Command(BaseCommand):
    """
    Creates a JSON file with all regions of France.
    The data source is a JSON file that comes from api.gouv.fr's GeoAPI.

    Usage:
    django-admin generate_regions

    Output example:
    {"nom":"Guadeloupe","code":"01"}
    """

    help = "Create a JSON file with all regions of France."

    def handle(self, **options):

        url = f"{settings.API_GEO_BASE_URL}/regions"

        r = requests.get(url)

        file_path = f"{CURRENT_DIR}/data/regions.json"
        with open(file_path, "wb") as f:
            f.write(r.content)

        self.stdout.write("-" * 80)
        self.stdout.write(f"File available at `{file_path}`.")
        self.stdout.write("Done.")
