import time

import requests

from lemarche.labels.models import Label
from lemarche.siaes.models import Siae, SiaeLabel
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


API_AGENCE_BIO_ENDPOINT = "https://opendata.agencebio.org/api/gouv/operateurs/"


class Command(BaseCommand):
    """
    https://api.gouv.fr/les-api/api-professionnels-bio
    - limite de l'API : "50 appels / seconde / IP"

    Usage:
    python manage.py api_agence_bio --dry-run
    python manage.py api_agence_bio
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, dry_run=False, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("API Agence Bio")

        label_rge = Label.objects.get(name="Agence Bio")
        siaes = Siae.objects.all()
        self.stdout_info(f"SIAE count: {siaes.count()}")

        progress = 0
        results = {"success": 0, "error": 0}

        for siae in siaes:
            # fetch data
            url = f"{API_AGENCE_BIO_ENDPOINT}?siret={siae.siret}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()

            # add label to siae
            if len(data["items"]):
                if not dry_run:
                    # siae.labels.add(label_rge)
                    SiaeLabel.objects.create(siae=siae, label=label_rge)
                results["success"] += 1

            progress += 1
            if (progress % 50) == 0:
                time.sleep(2)
            if (progress % 500) == 0:
                print(f"{progress}...")

        msg_success = [
            "----- Recap: API Agence Bio -----",
            f"Done! Processed {siaes.count()} siae",
            f"success count: {results['success']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)
        if not dry_run:
            api_slack.send_message_to_channel("\n".join(msg_success))
