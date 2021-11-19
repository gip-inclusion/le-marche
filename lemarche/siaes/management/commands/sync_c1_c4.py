import os
import re

import psycopg2
import psycopg2.extras
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.utils import timezone
from stdnum.fr import siret

from lemarche.siaes.constants import DEPARTMENT_TO_REGION
from lemarche.siaes.models import Siae
from lemarche.utils.data import rename_dict_key


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
    Usage:
    - poetry run python manage.py sync_c1_c4 --dry-run
    - poetry run python manage.py sync_c1_c4
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no writes")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Sync script between C1 & C4...")

        self.stdout.write("Step 1: fetching C1 data")
        c1_list = self.c1_export()

        self.stdout.write("Step 2: update C4 data")
        # count before
        siae_total_before = Siae.objects.all().count()
        siae_active_before = Siae.objects.filter(is_active=True).count()
        siae_delisted_before = Siae.objects.filter(is_delisted=True).count()
        self.c4_update(c1_list, dry_run)

        # count after
        siae_total_after = Siae.objects.all().count()
        siae_active_after = Siae.objects.filter(is_active=True).count()
        siae_delisted_after = Siae.objects.filter(is_delisted=True).count()

        print("Siae total (before / after):", siae_total_before, siae_total_after)
        print("Siae active (before / after):", siae_active_before, siae_active_after)
        print("Siae delisted (before / after):", siae_delisted_before, siae_delisted_after)

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
        for c1_siae in c1_list_temp[:1]:
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

        print(c1_list_cleaned)

        return c1_list_cleaned

    def c4_update(self, c1_list, dry_run):
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
            Siae.objects.create(**c1_siae)
            self.stdout.write("New Siae created")

    def c4_update_siae(self, c1_siae, c4_siae, dry_run):
        self.stdout.write("Updating Siae...")

        if dry_run:
            return

        # clean fields
        rename_dict_key(c1_siae, "id", "c1_id")

        # TODO...

        # other fields
        c1_siae["is_delisted"] = True if not c1_siae["is_active"] else False
        c1_siae["c1_last_sync_date"] = timezone.now()

        if not dry_run:
            # Siae.objects.update()  # avoid updated_at change
            self.stdout.write("Siae updated")
