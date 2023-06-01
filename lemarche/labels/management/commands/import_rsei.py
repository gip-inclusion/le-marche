import csv

from lemarche.labels.models import Label
from lemarche.siaes.models import Siae, SiaeLabel
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


LABEL_NAME = "RSEi"
SIRET_COLUMN_NAME = "Numéro de SIRET"


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

        label = Label.objects.get(name=LABEL_NAME)
        siaes = Siae.objects.all()
        self.stdout_info(f"SIAE count: {siaes.count()}")

        progress = 0
        results = {"success": 0, "error": 0}

        file_row_list = read_csv(options["file"])
        self.stdout_info(f"{LABEL_NAME} file row count: {len(file_row_list)}")

        for row_item in file_row_list:
            row_item_siret = row_item[SIRET_COLUMN_NAME].replace(" ", "")
            qs = Siae.objects.filter(siret=row_item_siret)
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
            f"----- Recap: Import {LABEL_NAME} -----",
            f"Done! Processed {siaes.count()} siae",
            f"success count: {results['success']}/{siaes.count()}",
            f"error count: {results['error']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)
        if not options["dry_run"]:
            api_slack.send_message_to_channel("\n".join(msg_success))
