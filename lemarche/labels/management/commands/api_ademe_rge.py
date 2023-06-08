import time

import requests
from django.utils import timezone

from lemarche.labels.models import Label
from lemarche.siaes.models import Siae, SiaeLabel
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


LABEL_NAME = "ADEME RGE"
LABEL_SLUG = "rge"
LABEL_API_ENDPOINT = "https://data.ademe.fr/data-fair/api/v1/datasets/liste-des-entreprises-rge-2/lines"
# LABEL_API_ENDPOINT_ALT = "https://data.ademe.fr/data-fair/api/v1/datasets/liste-des-entreprises-rge-2/values/siret"


class Command(BaseCommand):
    """
    https://api.gouv.fr/documentation/api_professionnels_rge

    Rules
    "Un utilisateur anonyme ne peut pas effectuer plus de 100 requêtes par interval de 5 secondes"


    Usage: python manage.py api_ademe_rge --dry-run
    Usage: python manage.py api_ademe_rge
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info(f"API {LABEL_NAME}")

        label = Label.objects.get(slug=LABEL_SLUG)
        siaes = Siae.objects.all()
        siae_label = SiaeLabel.objects.filter(label=label)
        self.stdout_info("-" * 80)
        self.stdout_info(f"SIAE count: {siaes.count()}")
        self.stdout_info(f"SIAE with {LABEL_NAME} label count: {siae_label.count()}")
        if not options["dry_run"]:
            siae_label.delete()
            self.stdout_info("Deleted!")

        progress = 0
        results = {"success": 0, "error": 0}

        self.stdout_info("-" * 80)
        self.stdout_info("Querying the API for each Siae...")
        for siae in siaes:
            if siae.siret:
                # fetch data
                url = f"{LABEL_API_ENDPOINT}?qs=siret:{siae.siret}"
                # url = f"{LABEL_API_ENDPOINT_ALT}?q={siae.siret}"
                r = requests.get(url)
                r.raise_for_status()
                # data = r.json()
                data = r.json()["results"]

                # add label to siae
                if len(data):
                    if not options["dry_run"]:
                        # siae.labels.add(label)
                        log_item = {
                            "action": "create",
                            "timestamp": timezone.now().isoformat(),
                            "source": LABEL_API_ENDPOINT,
                            "metadata": data[0],
                        }
                        SiaeLabel.objects.create(siae=siae, label=label, logs=[log_item])
                    results["success"] += 1

            progress += 1
            if (progress % 50) == 0:
                time.sleep(2)
            if (progress % 500) == 0:
                print(f"{progress}...")

        msg_success = [
            f"----- Recap: API {LABEL_NAME} -----",
            f"Done! Processed {siaes.count()} siae",
            f"success count: {results['success']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)

        if not options["dry_run"]:
            label.data_last_sync_date = timezone.now()
            log_item = {
                "action": "data_sync",
                "timestamp": timezone.now().isoformat(),
                "source": LABEL_API_ENDPOINT,
                "metadata": {"siae_count": siaes.count(), "success_count": results["success"]},
            }
            label.logs.append(log_item)
            label.save()

            api_slack.send_message_to_channel("\n".join(msg_success))
