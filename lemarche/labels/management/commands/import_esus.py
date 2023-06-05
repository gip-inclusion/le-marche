import csv

from django.utils import timezone

from lemarche.labels.models import Label
from lemarche.siaes.models import Siae, SiaeLabel
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


LABEL_NAME = "ESUS"
LABEL_SLUG = "esus"
LABEL_SIRET_COLUMN_NAME = "numero_siren"


def read_csv(file_path):
    row_list = list()

    with open(file_path) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):
            row_list.append(row)

    return row_list


class Command(BaseCommand):
    """
    https://www.tresor.economie.gouv.fr/banque-assurance-finance/finance-sociale-et-solidaire/liste-nationale-agrements-esus

    Usage:
    python manage.py import_esus --file <PATH.csv> --dry-run
    python manage.py import_esus --file <PATH.csv>
    """

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True)
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Import {LABEL_NAME}")

        label = Label.objects.get(slug=LABEL_SLUG)
        siaes = Siae.objects.all()
        self.stdout_info(f"SIAE count: {siaes.count()}")

        progress = 0
        results = {"success": 0, "error": 0}

        file_row_list = read_csv(options["file"])
        self.stdout_info(f"{LABEL_NAME} file row count: {len(file_row_list)}")

        for row_item in file_row_list:
            row_item_siren = row_item[LABEL_SIRET_COLUMN_NAME].replace(" ", "")
            qs = Siae.objects.filter(siret__startswith=row_item_siren)
            if qs.exists():
                if qs.count() > 1:
                    results["error"] += 1
                else:
                    if not options["dry_run"]:
                        # qs.first().labels.add(label)
                        SiaeLabel.objects.create(siae=qs.first(), label=label)
                    results["success"] += 1

            progress += 1
            if (progress % 500) == 0:
                print(f"{progress}...")

        msg_success = [
            "----- Recap: Import {LABEL_NAME} -----",
            f"Done! Processed {siaes.count()} siae",
            f"Success count: {results['success']}/{siaes.count()}",
            f"Error count: {results['error']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)

        if not options["dry_run"]:
            label.data_last_sync_date = timezone.now()
            log_item = {
                "action": "data_sync",
                "source": options["file"],
                "results": {"success_count": results["success"], "error_count": results["error"]},
            }
            label.logs.append(log_item)
            label.save()

            api_slack.send_message_to_channel("\n".join(msg_success))
