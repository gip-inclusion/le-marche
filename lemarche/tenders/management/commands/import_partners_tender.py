import csv
import os

from django.core.management.base import BaseCommand
from django.db.models import Q

from lemarche.perimeters.models import Perimeter
from lemarche.tenders.models import PartnerShareTender


class Command(BaseCommand):
    """
    This script is used to import a list of partners from a csv
    To use it, get the csv list and call it list_partners_share_tenders.csv"

    Usage:
    python manage.py import_partners_tender
    python manage.py import_partners_tender --name test.csv
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            default="list_partners_share_tenders.csv",
            help="nom du fichier par défaut list_partners_share_tenders.csv",
        )

    def handle(self, *args, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Updating Siae count fields...")

        # # Step 1: build Siae queryset
        # siae_queryset = Siae.objects.prefetch_related(
        #     "users", "sectors", "networks", "offers", "client_references", "labels", "images"
        # ).all()
        # if options["id"]:
        #     siae_queryset = siae_queryset.filter(id=options["id"])
        # self.stdout.write(f"Found {siae_queryset.count()} Siae")

        # # Step 2: loop on each Siae
        # progress = 0
        # for index, siae in enumerate(siae_queryset):
        #     user_count = siae.users.count()
        #     sector_count = siae.sectors.count()
        #     network_count = siae.networks.count()
        #     offer_count = siae.offers.count()
        #     client_reference_count = siae.client_references.count()
        #     label_count = siae.labels.count()
        #     image_count = siae.images.count()

        #     # Step 3: update count fields
        #     # why do we use .update() instead of .save() ? To avoid updating the 'updated_at' fieldS
        #     Siae.objects.filter(id=siae.id).update(
        #         user_count=user_count,
        #         sector_count=sector_count,
        #         network_count=network_count,
        #         offer_count=offer_count,
        #         client_reference_count=client_reference_count,
        #         label_count=label_count,
        #         image_count=image_count,
        #     )

        #     progress += 1
        #     if (progress % 500) == 0:
        #         self.stdout.write(f"{progress}...")
        file_name = os.path.dirname(os.path.realpath(__file__)) + "/" + options["name"]
        with open(file_name) as file:
            reader = csv.reader(file)
            next(reader)  # Advance past the header
            progress = 0
            for row in reader:
                self.stdout.write(f"{row}")
                name, _, _, email, perimeter_name, _, _ = row
                partner = PartnerShareTender.objects.filter(name=name)
                partner_exist = partner.count() > 0
                if not partner_exist and perimeter_name and perimeter_name != "France entière":
                    partner = PartnerShareTender(name=name, contact_email_list=[email])
                    partner.save()
                    perimeters = Perimeter.objects.filter(name=perimeter_name).distinct()
                    conditions = Q(name=perimeter_name)
                    for perimeter in perimeters:
                        if perimeter.kind == Perimeter.KIND_REGION:
                            conditions |= Q(region_code=perimeter.insee_code[1:])
                    if conditions != Q(name=perimeter_name):
                        perimeters = Perimeter.objects.filter(conditions).distinct()

                    if perimeters:
                        print(f"Ajout de {len(perimeters)} perimeters")
                        partner.perimeters.add(*perimeters)
                else:
                    if partner_exist:
                        partner[0].contact_email_list.append(email)
                        partner[0].save()
                progress += 1
                if (progress % 50) == 0:
                    self.stdout.write(f"{progress}...")
            self.stdout.write("Done")
