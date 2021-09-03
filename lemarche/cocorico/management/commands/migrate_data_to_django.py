import re
import pymysql

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models.fields import BooleanField, DateTimeField

from lemarche.siaes.models import Siae, SiaeNetwork
from lemarche.sectors.models import Sector, SectorGroup


C4_DSN = "<MYSQL-URL>"

DIRECTORY_EXTRA_KEYS = [
    "latitude", "longitude", "geo_range", "pol_range",
    # "presta_type",
    "sector",  # string 'list' with ' - ' seperator. map to Sector
]

DIRECTORY_BOOLEAN_FIELDS = [field.name for field in Siae._meta.fields if type(field) == BooleanField]
DIRECTORY_DATE_FIELDS = [field.name for field in Siae._meta.fields if type(field) == DateTimeField]
NETWORK_DATE_FIELDS = [field.name for field in SiaeNetwork._meta.fields if type(field) == DateTimeField]
SECTOR_DATE_FIELDS = [field.name for field in Sector._meta.fields if type(field) == DateTimeField]


def dsn2params(dsn):
    # PyMySQL doesn't support URI connection strings
    p = re.compile(r'mysql:\/\/(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>[^\/]+)\/(?P<db>.*)')
    m = re.match(p, dsn)
    d = m.groupdict()
    d['port'] = int(d['port'])
    return d

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

def make_aware_dates(elem, date_keys):
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


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py migrate_data_to_django
    """

    def handle(self, *args, **options):

        mysql_params = dsn2params(C4_DSN)
        connMy = pymysql.connect(**mysql_params)

        try:
            with connMy.cursor(pymysql.cursors.DictCursor) as cur:
                self.migrate_network(cur)
                # self.migrate_sector(cur)
                self.migrate_directory(cur)
                self.migrate_directory_network(cur)
        except Exception as e:
            # logger.exception(e)
            print(e)
            connMy.rollback()
        finally:
            connMy.close()


    def migrate_sector(cur):
        """
        """
        cur.execute("SELECT * FROM listing_category")  # listing_category_translation
        resp = cur.fetchall()

        # s = set([elem["name"] for elem in resp])
        # print(s)


    def migrate_network(self, cur):
        """
        - fields 'accronym' and 'siret' are always empty
        """
        SiaeNetwork.objects.all().delete()

        cur.execute("SELECT * FROM network")
        resp = cur.fetchall()

        # s = set([elem["siret"] for elem in resp])
        # print(s)

        for elem in resp:
            # cleanup dates
            cleanup_date_field_names(elem)
            make_aware_dates(elem, NETWORK_DATE_FIELDS)
            
            # remove useless keys
            [elem.pop(key) for key in ["accronym", "siret"]]
            
            SiaeNetwork.objects.create(**elem)


    def migrate_directory(self, cur):
        """
        """
        Siae.objects.all().delete()

        cur.execute("SELECT * FROM directory")
        resp = cur.fetchall()
        # print(len(resp))
        
        # s = set([elem["c4_id"] for elem in resp])
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
            make_aware_dates(elem, DIRECTORY_DATE_FIELDS)
                    
            
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


    def migrate_directory_network(self, cur):
        """
        elem exemple: {'directory_id': 270, 'network_id': 8}
        """
        Siae.networks.through.objects.all().delete()

        cur.execute("SELECT * FROM directory_network")
        resp = cur.fetchall()
        print(len(resp))
        print(resp[0])

        for elem in resp:
            siae = Siae.objects.get(pk=elem["directory_id"])
            siae.networks.add(elem["network_id"])
