import os
import re
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from stdnum.fr import siret

from lemarche.siaes.constants import DEPARTMENT_TO_REGION
from lemarche.siaes.models import Siae
from lemarche.utils.data import rename_dict_key


UPDATE_FIELDS = [
    "is_delisted",
    "c1_last_sync_date",
]


def map_siae_presta_type(siae_kind):
    if siae_kind:
        if siae_kind in ["ETTI", "AI"]:
            return [Siae.PRESTA_DISP]
        return [Siae.PRESTA_PREST, Siae.PRESTA_BUILD]
    return None


def map_siae_nature(siae_source):
    if siae_source:
        if siae_source in ["ASP", "GEIQ", "EA_EATT"]:
            return Siae.NATURE_HEAD_OFFICE
        if siae_source == "USER_CREATED":
            return Siae.NATURE_ANTENNA
    return None


class Command(BaseCommand):
    """
    What does the script do?
    It syncs the list of siae (creates new, updates existing) from C1 to C4.

    Steps:
    1. First we fetch all the siae from C1
    2. Then we loop on each of them, to create or update it (if siae with c1_id already exists)
    3. Don't forget to delist the siae who were not updated or inactive

    Usage:
    - poetry run python manage.py sync_c1_c4 --dry-run
    - poetry run python manage.py sync_c1_c4
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no writes")

    def handle(self, dry_run=False, **options):
        if not os.environ.get("C1_DSN"):
            raise CommandError("Missing C1_DSN in env")

        self.stdout.write("-" * 80)
        self.stdout.write("Sync script between C1 & C4...")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: fetching C1 data")
        c1_list = self.c1_export()

        self.stdout.write("-" * 80)
        self.stdout.write("Step 2: update C4 data")
        # count before
        siae_total_before = Siae.objects.all().count()
        siae_active_before = Siae.objects.filter(is_active=True).count()
        siae_delisted_before = Siae.objects.filter(is_delisted=True).count()

        self.c4_update(c1_list, dry_run)
        self.c4_delist_old_siae(dry_run)

        # count after
        siae_total_after = Siae.objects.all().count()
        siae_active_after = Siae.objects.filter(is_active=True).count()
        siae_delisted_after = Siae.objects.filter(is_delisted=True).count()

        self.stdout.write("-" * 80)
        self.stdout.write("Done ! Some stats...")
        created_count = siae_total_after - siae_total_before
        updated_count = len(c1_list) - created_count
        self.stdout.write(f"Siae total: before {siae_total_before} / after {siae_total_after} / +{created_count}")
        self.stdout.write(f"Siae updated: {updated_count}")
        self.stdout.write(f"Siae active: before {siae_active_before} / after {siae_active_after}")
        self.stdout.write(
            f"Siae inactive: before {siae_total_before - siae_active_before} / after {siae_total_after - siae_active_after}"  # noqa
        )
        self.stdout.write(f"Siae delisted: before {siae_delisted_before} / after {siae_delisted_after}")

    def c1_export(self):
        sql = """
        SELECT
        siae.id as id,
        siae.siret,
        siae.naf,
        siae.kind,
        siae.name,
        siae.brand,
        siae.phone,
        siae.email,
        siae.website,
        siae.description,
        siae.address_line_1,
        siae.address_line_2,
        siae.post_code,
        siae.city,
        siae.department,
        siae.source,
        ST_X(siae.coords::geometry) AS longitude,
        ST_Y(siae.coords::geometry) AS latitude,
        convention.is_active as is_active,
        ad.admin_name as admin_name,
        ad.admin_email as admin_email
        FROM siaes_siae AS siae
        LEFT OUTER JOIN siaes_siaeconvention AS convention
            ON convention.id = siae.convention_id
        LEFT OUTER JOIN (
            SELECT
                m.siae_id as siae_id,
                u.username as admin_name,
                u.email as admin_email
            FROM
            siaes_siaemembership m
            JOIN users_user u
                ON m.user_id = u.id
            WHERE m.is_admin = True
        ) ad ON ad.siae_id = siae.id
        """
        conn = psycopg2.connect(os.environ.get("C1_DSN"))
        c1_list_temp = list()

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql)
            response = cur.fetchall()
            for row in response:
                c1_list_temp.append(dict(row))

        # clean fields
        c1_list_cleaned = list()
        for c1_siae in c1_list_temp:
            c1_list_cleaned.append(
                {
                    **c1_siae,
                    "region": DEPARTMENT_TO_REGION.get(c1_siae["department"], None),
                    "presta_type": map_siae_presta_type(c1_siae["kind"]),
                    "nature": map_siae_nature(c1_siae["source"]),
                    # "is_delisted": c1_siae["is_active"] != False,
                    "siret_is_valid": siret.is_valid(c1_siae["siret"]),
                }
            )

        self.stdout.write(f"Found {len(c1_list_cleaned)} Siae in C1")
        return c1_list_cleaned

    def c4_update(self, c1_list, dry_run):
        """
        Loop on c1_list and figure out if each siae needs to be created OR already exists (update)
        """
        for c1_siae in c1_list:
            # if force_siret and c1['siret'] != force_siret:
            #     continue
            try:
                c4_siae = Siae.objects.get(c1_id=c1_siae["id"])
                self.c4_update_siae(c1_siae, c4_siae, dry_run)
            except Siae.DoesNotExist:
                self.c4_create_siae(c1_siae)

    def c4_create_siae(self, c1_siae, dry_run):
        self.stdout.write("Creating Siae...")

        # clean fields
        rename_dict_key(c1_siae, "id", "c1_id")
        c1_siae["description"] = ""
        c1_siae["phone"] = re.sub("[^0-9]", "", c1_siae["phone"])

        # create address
        c1_siae["address"] = c1_siae["address_line_1"] + " " + c1_siae["address_line_2"]
        del c1_siae["address_line_1"]
        del c1_siae["address_line_2"]

        # create coords from latitude & longitude
        if "latitude" in c1_siae and "longitude" in c1_siae:
            if c1_siae["latitude"] and c1_siae["longitude"]:
                coords = {"type": "Point", "coordinates": [float(c1_siae["longitude"]), float(c1_siae["latitude"])]}
                c1_siae["coords"] = GEOSGeometry(f"{coords}")  # Feed `GEOSGeometry` with GeoJSON.
            del c1_siae["latitude"]
            del c1_siae["longitude"]

        # init contact fields
        c1_siae["contact_website"] = c1_siae["website"]
        c1_siae["contact_email"] = c1_siae["email"]
        c1_siae["contact_phone"] = c1_siae["phone"]

        # TODO: call API Entreprise

        # other fields
        c1_siae["is_delisted"] = False
        c1_siae["c1_last_sync_date"] = timezone.now()

        # create object
        if not dry_run:
            siae = Siae.objects.create(**c1_siae)
            self.stdout.write(f"New Siae created / {siae.id} / {siae.siret}")

    def c4_update_siae(self, c1_siae, c4_siae, dry_run):
        self.stdout.write("Updating Siae...")

        if dry_run:
            return

        # other fields
        c1_siae["is_delisted"] = True if not c1_siae["is_active"] else False
        c1_siae["c1_last_sync_date"] = timezone.now()

        # keep only certain fields for update
        [c1_siae.pop(key) for key in c1_siae if key not in UPDATE_FIELDS]

        if not dry_run:
            Siae.objects.filter(c1_id=c4_siae.c1_id).update(**c1_siae)  # avoid updated_at change
            self.stdout.write(f"Siae updated / {c4_siae.id} / {c4_siae.siret}")

    def c4_delist_old_siae(self, dry_run):
        """
        Which Siae should we delist?
        - the existing ones who haven't been updated
        - all the ones who have is_active as False
        """
        if not dry_run:
            yesterday = datetime.now() - timedelta(days=1)
            Siae.objects.exclude(c1_sync_skip=True).filter(
                c1_last_sync_date__lt=timezone.make_aware(yesterday)
            ).update(is_delisted=True)
            Siae.objects.filter(is_active=False).update(is_delisted=True)
