import csv

from lemarche.labels.models import Label
from lemarche.siaes.models import Siae, SiaeLabel
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


def read_csv(file_path):
    esus_list = list()

    with open(file_path) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):
            esus_list.append(row)

    return esus_list


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
        self.stdout_info("Import ESUS")

        label_esus = Label.objects.get(name="ESUS")
        siaes = Siae.objects.all()
        self.stdout_info(f"SIAE count: {siaes.count()}")

        progress = 0
        results = {"success": 0, "error": 0}

        esus_list = read_csv(options["file"])
        self.stdout_info(f"ESUS count: {len(esus_list)}")

        for esus_item in esus_list:
            esus_item_siren = esus_item["numero_siren"].replace(" ", "")
            qs = Siae.objects.filter(siret__startswith=esus_item_siren)
            if qs.exists():
                if qs.count() > 1:
                    results["error"] += 1
                else:
                    if not options["dry_run"]:
                        # qs.first().labels.add(label_esus)
                        SiaeLabel.objects.create(siae=qs.first(), label=label_esus)
                    results["success"] += 1

            progress += 1
            if (progress % 500) == 0:
                print(f"{progress}...")

        msg_success = [
            "----- Recap: Import ESUS -----",
            f"Done! Processed {siaes.count()} siae",
            f"success count: {results['success']}/{siaes.count()}",
            f"error count: {results['error']}/{siaes.count()}",
        ]
        self.stdout_messages_success(msg_success)
        if not options["dry_run"]:
            api_slack.send_message_to_channel("\n".join(msg_success))
