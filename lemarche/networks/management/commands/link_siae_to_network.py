import csv

from lemarche.networks.models import Network
from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    poetry run python manage.py link_siae_to_network --file file.csv --network 8 --siret-column 'SIRET' --dry-run
    """

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path to the CSV file")
        parser.add_argument("--network", type=int, help="Network ID")
        parser.add_argument("--siret-column", dest="siret_column", help="Name of the SIRET column")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        siae_list = list()
        network = Network.objects.get(id=options["network"])
        # header = list()

        self.stdout_info("-" * 80)
        self.stdout_info("Reading file...")

        with open(options["file"]) as csv_file:
            csvreader = csv.DictReader(csv_file, delimiter=",")
            # header = csvreader.fieldnames
            for index, row in enumerate(csvreader):
                row["index"] = index + 2
                siae_list.append(row)

        self.stdout_info("-" * 80)
        self.stdout_info(f"Found {len(siae_list)} siae. Running for loop...")

        siae_missing = 0
        siae_has_network = 0
        siae_network_added = 0

        for index, s in enumerate(siae_list):
            print("====================")
            # print(index)
            # print(s[options["siret_column"]])
            siae = None
            try:
                siae = Siae.objects.get(siret=s[options["siret_column"]])
                if network in siae.networks.all():
                    # print("Siae Network already linked")
                    siae_list[index]["Déjà ajouté"] = "Oui"
                    siae_has_network += 1
                else:
                    # print("Siae Network new links")
                    siae_list[index]["Ajouté"] = "Oui"
                    siae_network_added += 1
                    if not options["dry_run"]:
                        siae.networks.add(network)
            except:  # noqa
                # print("Siae missing", s[options["siret_column"]])
                siae_list[index]["SIRET manquant"] = "Oui"
                siae_missing += 1

        print("====================")
        print("Total", len(siae_list))
        print("Siae missing", siae_missing)
        print("Siae Network already linked", siae_has_network)
        print("Siae Network new links", siae_network_added)

        # with open(f"{file_path}-enriched.csv", "w") as csv_file:
        #     fieldnames = ["index"] + header + ["SIRET manquant", "Inscrite", "Déjà ajouté", "Ajouté"]
        #     writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        #     writer.writeheader()
        #     for s in fei_siae_list:
        #         writer.writerow(s)
