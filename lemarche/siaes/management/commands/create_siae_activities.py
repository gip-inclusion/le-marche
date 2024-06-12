from lemarche.siaes.models import Siae, SiaeActivity
from lemarche.utils.commands import BaseCommand
from lemarche.utils.data import reset_app_sql_sequences


class Command(BaseCommand):
    """
    Script to generate SiaeActivities from Siae data
    Will delete all existing SiaeActivities !!

    Usage:
    poetry run python manage.py create_siae_activities --dry-run
    poetry run python manage.py create_siae_activities
    """

    help = ""

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Script to create SiaeActivities...")

        # Step 1: overview
        self.stdout_info("-" * 80)
        siae_qs = Siae.objects.all()
        siae_with_sectors_qs = siae_qs.filter(sectors__isnull=False).distinct()
        siae_activity_qs = SiaeActivity.objects.all()
        self.stdout_info(f"Siae count: {siae_qs.count()}")
        self.stdout_info(f"Siae with sectors count: {siae_with_sectors_qs.count()}")
        self.stdout_info(f"SiaeActivity count: {siae_activity_qs.count()}")

        if not options["dry_run"]:
            # Step 2: clear existing SiaeActivities
            self.stdout_info("-" * 80)
            self.stdout_info("Deleting existing SiaeActivities")
            SiaeActivity.objects.all().delete()
            reset_app_sql_sequences("siaes")

            # Step 3: create SiaeActivities
            self.stdout_info("-" * 80)
            self.stdout_info("Creating SiaeActivities")
            for siae in siae_qs:
                self.create_siae_activities(siae)

            # Recap
            self.stdout_info("-" * 80)
            siae_activities_created = SiaeActivity.objects.count()
            msg_success = [
                "----- Create SiaeActivities -----",
                f"Done! Processed {siae_with_sectors_qs.count()} Siaes with sectors (out of {siae_qs.count()} Siaes)",
                f"Created {siae_activities_created} SiaeActivities",
            ]
            self.stdout_messages_success(msg_success)

    def create_siae_activities(self, siae: Siae):
        """
        - sector_group / sectors: we look at the existing siae sectors, and create an activity per sector group
        - presta_type: we look at the existing siae presta_types
        - location / geo_range / geo_range_custom_distance: we generate a perimeter from the siae address, and take the existing geo_range info  # noqa
        """
        if siae.sectors.count() == 0:
            self.stdout_warning(f"No sectors for {siae}")
            return

        # Get the siae location
        # TODO

        siae_sector_group_ids = list(set(siae.sectors.values_list("group", flat=True)))
        # For each SectorGroup, create a SiaeActivity
        for sector_group_id in siae_sector_group_ids:
            siae_activity = SiaeActivity.objects.create(
                siae=siae,
                sector_group_id=sector_group_id,
                presta_type=siae.presta_type,
                # location=siae.location,
                geo_range=siae.geo_range,
                geo_range_custom_distance=siae.geo_range_custom_distance,
            )
            siae_activity.sectors.set(siae.sectors.filter(group_id=sector_group_id))

        self.stdout_info(f"Created {len(siae_sector_group_ids)} activities for {siae}")
