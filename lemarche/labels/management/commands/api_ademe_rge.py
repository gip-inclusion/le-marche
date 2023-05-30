import time

import requests

# from lemarche.labels.models import Label
from lemarche.siaes.models import Siae

# from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


API_ADEME_RGE_ENDPOINT = "https://data.ademe.fr/data-fair/api/v1/datasets/liste-des-entreprises-rge-2/values/siret"


class Command(BaseCommand):
    """
    https://api.gouv.fr/documentation/api_professionnels_rge

    Usage: python manage.py api_ademe_rge
    """

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("API ADEME RGE")

        # label_rge = Label.objects.get(name="RGE")
        siaes = Siae.objects.all()
        self.stdout_info(f"SIAE count: {siaes.count()}")

        progress = 0
        results = {"success": 0, "error": 0}

        for siae in siaes:
            # fetch data
            url = f"{API_ADEME_RGE_ENDPOINT}?q={siae.siret}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()

            # add label to siae
            if len(data):
                # siae.labels.add(label_rge)
                results["success"] += 1

            progress += 1
            # "Un utilisateur anonyme ne peut pas effectuer plus de 100 requêtes par interval de 5 secondes"
            if (progress % 50) == 0:
                time.sleep(2)
            if (progress % 500) == 0:
                print(f"{progress}...")

        msg_success = [
            "----- Recap: API ADEME RGE -----",
            f"Done! Processed {siaes.count()} siae",
            f"success count: {results['success']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)
        # api_slack.send_message_to_channel("\n".join(msg_success))
