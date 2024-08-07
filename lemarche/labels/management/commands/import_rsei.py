import csv

from django.utils import timezone

from lemarche.labels.models import Label
from lemarche.siaes.models import Siae, SiaeLabel
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


LABEL_NAME = "RSEi"
LABEL_SLUG = "rsei"
LABEL_SIRET_COLUMN_NAME = "Numéro de SIRET"


def read_csv(file_path):
    row_list = list()

    with open(file_path) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):
            row_list.append(row)

    return row_list


class Command(BaseCommand):
    """
    https://certification.afnor.org/developpement-durable-rse/demarches-rse-sectorielles/label-rsei

    Rule:
    1 SIRET = 1 Siae (error if multiple)

    Usage:
    python manage.py import_rsei --file <PATH.csv> --dry-run
    python manage.py import_rsei --file <PATH.csv>
    """

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True)
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info(f"Import {LABEL_NAME}")

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

        file_row_list = read_csv(options["file"])
        self.stdout_info("-" * 80)
        self.stdout_info(f"{LABEL_NAME} file row count: {len(file_row_list)}")
        self.stdout_info("Importing...")

        for row_item in file_row_list:
            row_item_siret = row_item[LABEL_SIRET_COLUMN_NAME].replace(" ", "")
            qs = Siae.objects.filter(siret=row_item_siret)
            if qs.exists():
                if qs.count() > 1:
                    results["error"] += 1
                else:
                    if not options["dry_run"]:
                        # qs.first().labels.add(label)
                        log_item = {
                            "action": "create",
                            "timestamp": timezone.now().isoformat(),
                            "source": options["file"],
                            "metadata": row_item,
                        }
                        SiaeLabel.objects.create(siae=qs.first(), label=label, logs=[log_item])
                    results["success"] += 1

            progress += 1
            if (progress % 500) == 0:
                print(f"{progress}...")

        msg_success = [
            f"----- Recap: Import {LABEL_NAME} -----",
            f"Done! Processed {len(file_row_list)} rows",
            f"Success count: {results['success']}/{siaes.count()}",
            f"Error count: {results['error']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)

        if not options["dry_run"]:
            label.data_last_sync_date = timezone.now()
            log_item = {
                "action": "data_sync",
                "timestamp": timezone.now().isoformat(),
                "source": options["file"],
                "metadata": {
                    "siae_count": siaes.count(),
                    "row_count": len(file_row_list),
                    "success_count": results["success"],
                    "error_count": results["error"],
                },
            }
            label.logs.append(log_item)
            label.save()

            api_slack.send_message_to_channel("\n".join(msg_success))
