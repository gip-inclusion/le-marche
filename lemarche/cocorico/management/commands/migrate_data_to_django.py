import io
import re
import pymysql
from collections import Counter

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, IntegrityError
from django.db.models.fields import BooleanField, DateTimeField
from django.utils import timezone
from django.utils.text import slugify

from lemarche.siaes.models import Siae, SiaeOffer, SiaeLabel, SiaeClientReference
from lemarche.networks.models import Network
from lemarche.sectors.models import SectorGroup, Sector


DIRECTORY_EXTRA_KEYS = [
    "latitude", "longitude", "geo_range", "pol_range",
    "sector",  # string 'list' with ' - ' seperator. We can map to Sector. But we use instead the 'directory_category' table.
]

DIRECTORY_BOOLEAN_FIELDS = [field.name for field in Siae._meta.fields if type(field) == BooleanField]
DIRECTORY_DATE_FIELDS = [field.name for field in Siae._meta.fields if type(field) == DateTimeField]
NETWORK_DATE_FIELDS = [field.name for field in Network._meta.fields if type(field) == DateTimeField]
SECTOR_DATE_FIELDS = [field.name for field in Sector._meta.fields if type(field) == DateTimeField]


def dsn2params(dsn):
    # PyMySQL doesn't support URI connection strings
    p = re.compile(r'mysql:\/\/(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>[^\/]+)\/(?P<db>.*)')
    m = re.match(p, dsn)
    d = m.groupdict()
    d['port'] = int(d['port'])
    return d

def rename_field(elem, field_name_before, field_name_after):
    elem[field_name_after] = elem[field_name_before]
    elem.pop(field_name_before)

def integer_to_boolean(input_value):
    if input_value in [1]:
        return True
    elif input_value in [0, None]:
        return False
    return False

def cleanup_date_field_names(elem):
    if "createdAt" in elem:
        if elem["createdAt"]:
            elem["created_at"] = elem["createdAt"]
        elem.pop("createdAt")
    if "updatedAt" in elem:
        if elem["updatedAt"]:
            elem["updated_at"] = elem["updatedAt"]
        elem.pop("updatedAt")

def make_aware_dates(elem):
    date_keys = list(set(DIRECTORY_DATE_FIELDS + NETWORK_DATE_FIELDS + SECTOR_DATE_FIELDS))
    for key in date_keys:
            if key in elem:
                if elem[key]:
                    elem[key] = timezone.make_aware(elem[key])

def map_presta_type(input_value_byte):
    if input_value_byte:
        input_value_string = input_value_byte.decode()
        presta_type_mapping = {
            None: None,
            "0": [],
            "2": [Siae.PRESTA_DISP],
            "4": [Siae.PRESTA_PREST],
            "6": [Siae.PRESTA_DISP, Siae.PRESTA_PREST],
            "8": [Siae.PRESTA_BUILD],
            "10": [Siae.PRESTA_DISP, Siae.PRESTA_BUILD],
            "12": [Siae.PRESTA_PREST, Siae.PRESTA_BUILD],
            "14": [Siae.PRESTA_DISP, Siae.PRESTA_PREST, Siae.PRESTA_BUILD]
        }
        return presta_type_mapping[input_value_string]
    return None

def reset_app_sql_sequences(app_name):
    """
    To reset the id indexes of a given app (will impact *all* of the apps' tables)
    https://docs.djangoproject.com/en/3.1/ref/django-admin/#sqlsequencereset
    https://stackoverflow.com/a/44113124
    """
    print(f"Resetting SQL sequences for {app_name}...")
    output = io.StringIO()
    call_command('sqlsequencereset', app_name, stdout=output, no_color=True)
    sql = output.getvalue()
    with connection.cursor() as cursor:
        cursor.execute(sql)
    output.close()
    print("Done !")


class Command(BaseCommand):
    """
    Migrate from Symphony/MariaDB to Django/PostgreSQL

    directory --> Siae
    network --> Network
    directory_network --> M2M between Siae & Network
    listing_category & listing_category_translation --> Sector
    directory_listing_category --> M2M between Siae & Sector
    directory_label --> SiaeLabel ("Labels & certifications") + OneToMany between Siae & Label
    directory_offer --> SiaeOffer ("Prestations proposées") + OneToMany between Siae & Offer
    directory_client_image --> SiaeClientReference ("Références clients") + OneToMany between Siae & SiaeClientReference

    Usage: poetry run python manage.py migrate_data_to_django
    """
    def handle(self, *args, **options):

        mysql_params = dsn2params(settings.MYSQL_ADDON_DIRECT_URI)
        connMy = pymysql.connect(**mysql_params)

        try:
            with connMy.cursor(pymysql.cursors.DictCursor) as cur:
                self.migrate_siae(cur)
                self.migrate_network(cur)
                self.migrate_siae_network(cur)
                self.migrate_sector(cur)
                self.migrate_siae_sector(cur)
                self.migrate_siae_offer(cur)
                self.migrate_siae_label(cur)
                self.migrate_siae_client_reference(cur)
        except Exception as e:
            # logger.exception(e)
            print(e)
            connMy.rollback()
        finally:
            connMy.close()


    def migrate_siae(self, cur):
        """
        Migrate Siae data
        """
        print("Migrating Siae...")

        Siae.objects.all().delete()

        cur.execute("SELECT * FROM directory")
        resp = cur.fetchall()
        # print(len(resp))
        
        # s = set([elem["pol_range"] for elem in resp])
        # print(s)

        # elem = cur.fetchone()
        # print(elem)

        for elem in resp:
            # cleanup boolean fields
            for key in DIRECTORY_BOOLEAN_FIELDS:
                if key in elem:
                    elem[key] = integer_to_boolean(elem[key])

            # cleanup dates
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

            # cleanup presta_type
            if "presta_type" in elem:
                elem["presta_type"] = map_presta_type(elem["presta_type"])

            # remove useless keys
            [elem.pop(key) for key in DIRECTORY_EXTRA_KEYS]

            # create object
            try:
                first = Siae.objects.create(**elem)
                # print(first.__dict__)
            except Exception as e:
                print(e)

        print(f"Created {Siae.objects.count()} siaes !")


    def migrate_network(self, cur):
        """
        Migrate Network data

        Notes:
        - fields 'accronym' and 'siret' are always empty
        """
        print("Migrating Network...")

        Network.objects.all().delete()

        cur.execute("SELECT * FROM network")
        resp = cur.fetchall()

        # s = set([elem["siret"] for elem in resp])
        # print(s)

        for elem in resp:
            # cleanup dates
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

            # remove useless keys
            [elem.pop(key) for key in ["accronym", "siret"]]

            # add new keys
            elem["slug"] = slugify(elem["name"])

            # create object
            Network.objects.create(**elem)

        print(f"Created {Network.objects.count()} siae networks !")


    def migrate_siae_network(self, cur):
        """
        Migrate M2M data between Siae & Network

        Notes:
        - elem exemple: {'directory_id': 270, 'network_id': 8}
        """
        print("Migrating M2M between Siae & Network...")

        Siae.networks.through.objects.all().delete()

        cur.execute("SELECT * FROM directory_network")
        resp = cur.fetchall()
        # print(len(resp))
        # print(resp[0])

        for elem in resp:
            siae = Siae.objects.get(pk=elem["directory_id"])
            siae.networks.add(elem["network_id"])

        print(f"Created {Siae.networks.through.objects.count()} M2M objects !")


    def migrate_sector(self, cur):
        """
        Migrate Sector & SectorGroup data

        Notes:
        - the current implementation in Symphony is overly complex
        - we simplify it with a simple parent/child hierarchy
        """
        print("Migrating Sector & SectorGroup...")

        Sector.objects.all().delete()
        SectorGroup.objects.all().delete()
        reset_app_sql_sequences("sectors")

        cur.execute("SELECT * FROM listing_category")
        resp = cur.fetchall()

        # first we recreate the hierarchy Sector Group > Sector Children
        sector_group_list = []
        for elem in resp:
            if not elem["parent_id"]:
                # this is a group elem, create it if it doesn't exist yet
                sector_group_index = next((index for (index, s) in enumerate(sector_group_list) if s["id"] == elem["id"]), None)
                if sector_group_index is None:
                    sector_group_list.append({ "id": elem["id"], "children": [] })
            else:
                # this is a child elem
                sector_group_index = next((index for (index, s) in enumerate(sector_group_list) if s["id"] == elem["parent_id"]), None)
                if sector_group_index is None:
                    sector_group_list.append({ "id": elem["parent_id"], "children": [] })
                    sector_group_index = len(sector_group_list) - 1
                sector_group_list[sector_group_index]["children"].append(elem["id"])
        
        # print(sector_group_list)

        cur.execute("SELECT * FROM listing_category_translation")
        resp = cur.fetchall()

        # then we loop on the hierarchy to create the SectorGroup & Sector objects
        for sector_group_dict in sector_group_list:
            elem_data = next(s for (index, s) in enumerate(resp) if ((s["translatable_id"] == sector_group_dict["id"]) and (s["locale"] == "fr")))
            sector_group = SectorGroup.objects.create(pk=sector_group_dict["id"], name=elem_data["name"], slug=elem_data["slug"])
            for sector_id in sector_group_dict["children"]:
                elem_data = next(s for (index, s) in enumerate(resp) if ((s["translatable_id"] == sector_id) and (s["locale"] == "fr")))
                try:
                    Sector.objects.create(pk=sector_id, name=elem_data["name"], slug=elem_data["slug"], group=sector_group)
                except IntegrityError:  # sometimes the slugs are duplicated (e.g. "autre")
                    slug_fix = f"{elem_data['slug']}-{sector_group_dict['id']}"
                    Sector.objects.create(pk=sector_id, name=elem_data["name"], slug=slug_fix, group=sector_group)

        print(f"Created {SectorGroup.objects.count()} sector groups !")
        print(f"Created {Sector.objects.count()} sectors !")


    def migrate_siae_sector(self, cur):
        """
        Migrate M2M data between Siae & Sector

        Notes:
        - elem exemple: {'category_id': 270, 'listing_category_id': 8}
        """
        print("Migrating M2M between Siae & Sector...")

        Siae.sectors.through.objects.all().delete()

        cur.execute("SELECT * FROM directory_listing_category")
        resp = cur.fetchall()
        # print(len(resp))
        # print(resp[0])

        # Sometimes Siaes are linked to a SectorGroup instead of a Sector.
        # We ignore these cases
        for elem in resp:
            try:
                siae = Siae.objects.get(pk=elem["directory_id"])
                siae.sectors.add(elem["listing_category_id"])
            except:
                # print(elem)
                pass

        print(f"Created {Siae.sectors.through.objects.count()} M2M objects !")


    def migrate_siae_offer(self, cur):
        """
        Migrate SiaeOffer data
        """
        print("Migrating SiaeOffer...")

        SiaeOffer.objects.all().delete()

        cur.execute("SELECT * FROM directory_offer")
        resp = cur.fetchall()
        # print(len(resp))
        # print(resp[0])

        # l = [elem["source"] for elem in resp]
        # print(Counter(l))

        # elem = cur.fetchone()
        # print(elem)

        for elem in resp:
            # cleanup dates
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

            # rename fields
            rename_field(elem, "directory_id", "siae_id")

            # create object
            SiaeOffer.objects.create(**elem)

        print(f"Created {SiaeOffer.objects.count()} offers !")


    def migrate_siae_label(self, cur):
        """
        Migrate SiaeLabel data
        """
        print("Migrating SiaeLabel...")

        SiaeLabel.objects.all().delete()

        cur.execute("SELECT * FROM directory_label")
        resp = cur.fetchall()
        # print(len(resp))
        # print(resp[0])

        # l = [elem["source"] for elem in resp]
        # print(Counter(l))

        # elem = cur.fetchone()
        # print(elem)

        for elem in resp:
            # cleanup dates
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

            # rename fields
            rename_field(elem, "directory_id", "siae_id")

            # create object
            SiaeLabel.objects.create(**elem)

        print(f"Created {SiaeLabel.objects.count()} labels !")


    def migrate_siae_client_reference(self, cur):
        """
        Migrate SiaeClientReference data
        """
        print("Migrating SiaeClientReference...")

        SiaeClientReference.objects.all().delete()

        cur.execute("SELECT * FROM directory_client_image")
        resp = cur.fetchall()
        # print(len(resp))
        # print(resp[0])

        # l = [elem["position"] for elem in resp]
        # print(Counter(l))

        # elem = cur.fetchone()
        # print(elem)

        for elem in resp:
            # cleanup dates
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

            # rename fields
            rename_field(elem, "name", "image_name")
            rename_field(elem, "description", "name")
            rename_field(elem, "position", "order")
            rename_field(elem, "directory_id", "siae_id")

            # create object
            SiaeClientReference.objects.create(**elem)

        print(f"Created {SiaeClientReference.objects.count()} client references !")
