import re
import pymysql

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models.fields import BooleanField, DateTimeField

from lemarche.siaes.models import Siae, SiaeNetwork
from lemarche.sectors.models import Sector, SectorGroup


C4_DSN = "<INSERT-MYSQL-DB-URL-HERE>"

DIRECTORY_EXTRA_KEYS = [
    "latitude", "longitude", "geo_range", "pol_range",
    "presta_type",
    "sector",  # string 'list' with ' - ' seperator. map to Sector
]

DIRECTORY_BOOLEAN_FIELDS = [field.name for field in Siae._meta.fields if type(field) == BooleanField]

DIRECTORY_DATE_FIELDS = [field.name for field in Siae._meta.fields if type(field) == DateTimeField]


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


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py migrate_data_to_django
    """

    def handle(self, *args, **options):

        mysql_params = dsn2params(C4_DSN)
        connMy = pymysql.connect(**mysql_params)

        try:
            with connMy.cursor(pymysql.cursors.DictCursor) as cur:
                # self.migrate_network(cur)
                # self.migrate_sector(cur)
                self.migrate_directory(cur)
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
        print(resp)

    def migrate_network(self, cur):
        """
        - fields 'accronym' and 'siret' are always empty
        """
        SiaeNetwork.objects.all().delete()

        cur.execute("SELECT * FROM network")
        resp = cur.fetchall()
        print(resp)

        s = set([elem["siret"] for elem in resp])
        print(s)

        for elem in resp:
            [elem.pop(key) for key in ["accronym", "siret"]]
            cleanup_date_field_names(elem)
            SiaeNetwork.objects.create(**elem)
    
    def migrate_directory(self, cur):
        """
        """
        Siae.objects.all().delete()

        cur.execute("SELECT * FROM directory")
        # resp = cur.fetchall()
        # print(len(resp))
        
        # s = set([elem["c4_id"] for elem in resp])
        # print(s)

        # for elem in resp:
        #     if elem["sector"]:
        #         print(elem["c4_id"], elem["sector"])
        
        elem = cur.fetchone()
        print(elem)

        # cleanup boolean fields
        for key in DIRECTORY_BOOLEAN_FIELDS:
            if key in elem:
                elem[key] = integer_to_boolean(elem[key])
        
        # cleanup dates
        cleanup_date_field_names(elem)
        for key in DIRECTORY_DATE_FIELDS:
            if key in elem:
                print(key, elem[key])
                if elem[key]:
                    elem[key] = timezone.make_aware(elem[key])
        
        # remove useless keys
        [elem.pop(key) for key in DIRECTORY_EXTRA_KEYS]
        
        # create object
        first = Siae.objects.create(**elem)
        print(first)

