import os
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.models import Siae


UPDATE_FIELDS = [
    # table: saisies_mensuelles_iae
    # "asp_id",  # id_structure_asp
    "c2_etp_count",  # af_etp_postes_insertion
    "c2_etp_count_date_saisie",  # date_saisie
    "c2_etp_count_last_sync_date",
]


class Command(BaseCommand):
    """
    What does the script do?
    It syncs some specific fields from C2 to C4.

    Steps:
    1. First we fetch the data from C2 table
    2. Then we loop on each row, to update the corresponding siae

    Usage:
    - poetry run python manage.py sync_c2_c4 --dry-run
    - poetry run python manage.py sync_c2_c4
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no writes")

    def handle(self, dry_run=False, **options):
        if not os.environ.get("C2_DSN"):
            raise CommandError("Missing C2_DSN in env")

        self.stdout.write("-" * 80)
        self.stdout.write("Sync script between C2 & C4...")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: fetching C2 ETP data")
        c2_etp_list = self.c2_etp_export()

        self.stdout.write("-" * 80)
        self.stdout.write("Step 2: update C4 ETP data")
        # count before
        siae_total = Siae.objects.all().count()
        siae_etp_count_before = Siae.objects.exclude(c2_etp_count__isnull=True).count()

        self.c4_etp_update(c2_etp_list, dry_run)

        # count after
        siae_etp_count_after = Siae.objects.exclude(c2_etp_count__isnull=True).count()
        yesterday = datetime.now() - timedelta(days=1)
        siae_etp_udated = Siae.objects.filter(c2_etp_count_last_sync_date__gte=timezone.make_aware(yesterday)).count()

        self.stdout.write("-" * 80)
        self.stdout.write("Done ! Some stats...")
        etp_added_count = siae_etp_count_after - siae_etp_count_before
        etp_updated_count = siae_etp_udated - etp_added_count
        self.stdout.write(f"Siae total: {siae_total}")
        self.stdout.write(f"ETP count added: {etp_added_count}")
        self.stdout.write(f"ETP count updated: {etp_updated_count}")

    def c2_etp_export(self):
        sql = """
        SELECT
            DISTINCT ON (date_saisie, id_structure_asp)
            date_saisie,
            id_structure_asp,
            af_etp_postes_insertion
        FROM "saisies_mensuelles_iae"
        ORDER BY date_saisie DESC, id_structure_asp
        """
        conn = psycopg2.connect(os.environ.get("C2_DSN"))
        c2_etp_list_temp = list()

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql)
            response = cur.fetchall()
            for row in response:
                c2_etp_list_temp.append(dict(row))

        # clean fields
        # needed?

        self.stdout.write(f"Found {len(c2_etp_list_temp)} Unique id_asp / date_saisie")
        return c2_etp_list_temp

    def c4_etp_update(self, c2_etp_list, dry_run):
        """
        Loop on c2_etp_list and figure out if each siae needs to be updated or not
        Which Siae do we update?
        - if their c2_etp_count_last_sync_date is empty (new Siae which never when through the script)
        - or if c2_etp_count_last_sync_date < since_last_date_limit (to update the values regulary)
        """
        siaes_queryset = Siae.objects.all().order_by("id")
        since_last_date_limit = timezone.now() - timedelta(days=settings.API_QPV_RELATIVE_DAYS_TO_UPDATE)
        siaes_queryset = siaes_queryset.filter(
            (Q(c2_etp_count_last_sync_date__lte=since_last_date_limit) | Q(c2_etp_count_last_sync_date__isnull=True))
        )

        progress = 0
        for c2_siae in c2_etp_list:
            progress += 1
            if (progress % 1000) == 0:
                self.stdout.write(f"{progress}...")
            if not dry_run:
                if c2_siae["id_structure_asp"]:
                    siaes_queryset.filter(asp_id=c2_siae["id_structure_asp"]).update(
                        c2_etp_count=c2_siae["af_etp_postes_insertion"],
                        c2_etp_count_date_saisie=c2_siae["date_saisie"],
                        c2_etp_count_last_sync_date=timezone.now(),
                    )

        # also update Siae without asp_id
        siaes_queryset.filter(asp_id__isnull=True).update(c2_etp_count_last_sync_date=timezone.now())
