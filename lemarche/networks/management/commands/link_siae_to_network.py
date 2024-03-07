import csv

from lemarche.networks.models import Network
from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    poetry run python manage.py link_siae_to_network --file file.csv --network 8 --siret-column 'SIRET' --dry-run
    poetry run python manage.py link_siae_to_network --file file.csv --network 8 --siret-column 'SIRET'
    """

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path to the CSV file")
        parser.add_argument("--network", type=int, help="Network ID")
        parser.add_argument("--siret-column", dest="siret_column", help="Name of the SIRET column")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        siae_list = list()
        network = Network.objects.get(id=options["network"])

        self.stdout_info("-" * 80)
        self.stdout_info("Reading file...")

        with open(options["file"]) as csv_file:
            csvreader = csv.DictReader(csv_file, delimiter=",")
            for index, row in enumerate(csvreader):
                row["index"] = index + 2
                siae_list.append(row)

        self.stdout_info("-" * 80)
        self.stdout_info(f"Found {len(siae_list)} siae. Running for loop...")

        siae_missing = 0
        siae_has_network = 0
        siae_network_added = 0

        for index, s in enumerate(siae_list):
            siae = None
            try:
                siae = Siae.objects.get(siret=s[options["siret_column"]])
                if network in siae.networks.all():
                    # Siae Network already linked
                    siae_has_network += 1
                else:
                    # Siae Network new link
                    siae_network_added += 1
                    if not options["dry_run"]:
                        siae.networks.add(network)
            except:  # noqa
                # Siae missing
                siae_missing += 1

        print("====================")
        print("Total", len(siae_list))
        print("Siae missing", siae_missing)
        print("Siae Network already linked", siae_has_network)
        print("Siae Network new links", siae_network_added)
