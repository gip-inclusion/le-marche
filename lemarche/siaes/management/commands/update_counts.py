from django.core.management.base import BaseCommand

from lemarche.siaes.models import Siae


class Command(BaseCommand):
    """
    Goal: update the '_count' fields of each Siae

    Note: these fields should be updated automatically on each Siae save()

    Usage:
    python manage.py update_counts
    python manage.py update_counts --id 1
    """

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="Indiquer l'ID d'une structure")

    def handle(self, *args, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Updating Siae count fields...")

        # Step 1: build Siae queryset
        siae_queryset = Siae.objects.prefetch_related(
            "users", "sectors", "networks", "groups", "offers", "client_references", "labels", "images"
        ).all()
        if options["id"]:
            siae_queryset = siae_queryset.filter(id=options["id"])
        self.stdout.write(f"Found {siae_queryset.count()} Siae")

        # Step 2: loop on each Siae
        progress = 0
        for index, siae in enumerate(siae_queryset):
            # M2M
            user_count = siae.users.count()
            sector_count = siae.sectors.count()
            network_count = siae.networks.count()
            group_count = siae.groups.count()
            # FK
            offer_count = siae.offers.count()
            client_reference_count = siae.client_references.count()
            label_count = siae.labels_old.count()
            image_count = siae.images.count()

            # Step 3: update count fields
            # why do we use .update() instead of .save() ? To avoid updating the 'updated_at' fieldS
            Siae.objects.filter(id=siae.id).update(
                user_count=user_count,
                sector_count=sector_count,
                network_count=network_count,
                group_count=group_count,
                offer_count=offer_count,
                client_reference_count=client_reference_count,
                label_count=label_count,
                image_count=image_count,
            )

            progress += 1
            if (progress % 500) == 0:
                self.stdout.write(f"{progress}...")

        self.stdout.write("Done")
