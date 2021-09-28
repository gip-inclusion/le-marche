import os

import pymysql
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models.fields import BooleanField, DateTimeField
from django.utils import timezone
from django.utils.text import slugify

from lemarche.networks.models import Network
from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeLabel, SiaeOffer
from lemarche.users.models import User
from lemarche.utils.data import reset_app_sql_sequences


DIRECTORY_EXTRA_KEYS = [
    "sector",  # string 'list' with ' - ' seperator. We use instead the 'directory_category' table.
]
USER_EXTRA_KEYS = [
    "username",
    "username_canonical",
    "email_canonical",
    "slug",
    "salt",
    "password",
    "confirmation_token",
    "password_requested_at",
    "roles",
    "person_type",
    "birthday",
    "nationality",
    "country_of_residence",
    "profession",
    "mother_tongue",
    # "phone_prefix", "time_zone", "phone_verified", "email_verified", "id_card_verified",
    # "accept_survey", "accept_rgpd", "offers_for_pro_sector", "quote_promise",
    "iban",
    "bic",
    "bank_owner_name",
    "bank_owner_address",
    "annual_income",
    "nb_bookings_offerer",
    "nb_bookings_asker",
    "fee_as_asker",
    "fee_as_offerer",
    "average_rating_as_asker",
    "average_rating_as_offerer",
    "answer_delay",
    "nb_quotes_offerer",
    "nb_quotes_asker",
    "company_addr_string",
]

DIRECTORY_BOOLEAN_FIELDS = [field.name for field in Siae._meta.fields if type(field) == BooleanField]
USER_BOOLEAN_FIELDS = [field.name for field in User._meta.fields if type(field) == BooleanField]

DIRECTORY_DATE_FIELDS = [field.name for field in Siae._meta.fields if type(field) == DateTimeField]
NETWORK_DATE_FIELDS = [field.name for field in Network._meta.fields if type(field) == DateTimeField]
SECTOR_DATE_FIELDS = [field.name for field in Sector._meta.fields if type(field) == DateTimeField]
USER_DATE_FIELDS = [field.name for field in User._meta.fields if type(field) == DateTimeField]


def rename_field(elem, field_name_before, field_name_after):
    elem[field_name_after] = elem[field_name_before]
    elem.pop(field_name_before)


def integer_to_boolean(elem):
    boolean_keys = list(set(DIRECTORY_BOOLEAN_FIELDS + USER_BOOLEAN_FIELDS))
    for key in boolean_keys:
        if key in elem:
            if elem[key] in [1, "1"]:
                elem[key] = True
            elif elem[key] in [0, "0", None]:
                elem[key] = False
            else:
                elem[key] = False


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
    date_keys = list(set(DIRECTORY_DATE_FIELDS + NETWORK_DATE_FIELDS + SECTOR_DATE_FIELDS + USER_DATE_FIELDS))
    for key in date_keys:
        if key in elem:
            if elem[key]:
                elem[key] = timezone.make_aware(elem[key])


def map_siae_nature(input_value):
    if input_value:
        nature_mapping = {
            "siege": Siae.NATURE_HEAD_OFFICE,
            "antenne": Siae.NATURE_ANTENNA,
            "n/a": None,
            None: None,
        }
        return nature_mapping[input_value]
    return None


def map_siae_presta_type(input_value_byte):
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
            "14": [Siae.PRESTA_DISP, Siae.PRESTA_PREST, Siae.PRESTA_BUILD],
        }
        try:
            return presta_type_mapping[input_value_string]
        except:  # noqa
            pass
    return None


def map_geo_range(input_value_integer):
    geo_range_mapping = {
        3: Siae.GEO_RANGE_COUNTRY,
        2: Siae.GEO_RANGE_REGION,
        1: Siae.GEO_RANGE_DEPARTMENT,
        0: Siae.GEO_RANGE_CUSTOM,
        None: None,
    }
    try:
        return geo_range_mapping[input_value_integer]
    except:  # noqa
        return None


def map_user_kind(input_value_integer):
    if input_value_integer:
        user_kind_mapping = {
            None: None,
            # 1: User.KIND_PERSO,
            # 2: User.KIND_COMPANY,
            3: User.KIND_BUYER,
            4: User.KIND_SIAE,
            5: User.KIND_ADMIN,
            6: User.KIND_PARTNER,
        }
        try:
            return user_kind_mapping[input_value_integer]
        except:  # noqa
            pass
    return None


class Command(BaseCommand):
    """
    Migrate from Symphony/MariaDB to Django/PostgreSQL

    |--------------------------|---------------------------|
    |directory                 |Siae                       |
    |network                   |Network                    |
    |directory_network         |M2M between Siae & Network |
    |listing_category & listing_category_translation | Sector|
    |directory_listing_category|M2M between Siae & Sector  |
    |directory_label           |SiaeLabel ("Labels & certifications") + OneToMany between Siae & Label|
    |directory_offer           |SiaeOffer ("Prestations proposées") + OneToMany between Siae & Offer|
    |directory_client_image    |SiaeClientReference ("Références clients") + OneToMany between Siae & SiaeClientReference|  # noqa
    |user                      |User                       |
    |directory_user            |M2M between Siae & User    |

    Usage: poetry run python manage.py migrate_data_to_django
    """

    def handle(self, *args, **options):
        connMy = pymysql.connect(
            host=os.environ.get("MYSQL_ADDON_HOST"),
            port=int(os.environ.get("MYSQL_ADDON_PORT")),
            user=os.environ.get("MYSQL_ADDON_USER"),
            password=os.environ.get("MYSQL_ADDON_PASSWORD"),
            database=os.environ.get("MYSQL_ADDON_DB"),
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with connMy.cursor() as cur:
                self.migrate_siae(cur)
                # self.migrate_network(cur)
                # self.migrate_siae_network(cur)
                # self.migrate_sector(cur)
                # self.migrate_siae_sector(cur)
                # self.migrate_siae_offer(cur)
                # self.migrate_siae_label(cur)
                # self.migrate_siae_client_reference(cur)
                # self.migrate_user(cur)
                # self.migrate_siae_user(cur)
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

        # s = set([elem["is_qpv"] for elem in resp])
        # print(s)

        # elem = cur.fetchone()
        # print(elem)

        for elem in resp:
            # rename fields
            rename_field(elem, "geo_range", "geo_range_custom_distance")
            rename_field(elem, "pol_range", "geo_range")

            # cleanup fields
            cleanup_date_field_names(elem)
            make_aware_dates(elem)
            integer_to_boolean(elem)

            # cleanup nature
            if "nature" in elem:
                elem["nature"] = map_siae_nature(elem["nature"])

            # cleanup presta_type
            if "presta_type" in elem:
                elem["presta_type"] = map_siae_presta_type(elem["presta_type"])

            # cleanup geo_range
            if "geo_range" in elem:
                elem["geo_range"] = map_geo_range(elem["geo_range"])

            # remove useless keys
            [elem.pop(key) for key in DIRECTORY_EXTRA_KEYS]

            # create object
            try:
                Siae.objects.create(**elem)
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
                sector_group_index = next(
                    (index for (index, s) in enumerate(sector_group_list) if s["id"] == elem["id"]), None
                )
                if sector_group_index is None:
                    sector_group_list.append({"id": elem["id"], "children": []})
            else:
                # this is a child elem
                sector_group_index = next(
                    (index for (index, s) in enumerate(sector_group_list) if s["id"] == elem["parent_id"]), None
                )
                if sector_group_index is None:
                    sector_group_list.append({"id": elem["parent_id"], "children": []})
                    sector_group_index = len(sector_group_list) - 1
                sector_group_list[sector_group_index]["children"].append(elem["id"])

        # print(sector_group_list)

        cur.execute("SELECT * FROM listing_category_translation")
        resp = cur.fetchall()

        # then we loop on the hierarchy to create the SectorGroup & Sector objects
        for sector_group_dict in sector_group_list:
            elem_data = next(
                s
                for (index, s) in enumerate(resp)
                if ((s["translatable_id"] == sector_group_dict["id"]) and (s["locale"] == "fr"))
            )
            sector_group = SectorGroup.objects.create(
                pk=sector_group_dict["id"], name=elem_data["name"], slug=elem_data["slug"]
            )
            for sector_id in sector_group_dict["children"]:
                elem_data = next(
                    s
                    for (index, s) in enumerate(resp)
                    if ((s["translatable_id"] == sector_id) and (s["locale"] == "fr"))
                )
                try:
                    Sector.objects.create(
                        pk=sector_id, name=elem_data["name"], slug=elem_data["slug"], group=sector_group
                    )
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
            except:  # noqa
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
            # rename fields
            rename_field(elem, "directory_id", "siae_id")

            # cleanup fields
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

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
            # rename fields
            rename_field(elem, "directory_id", "siae_id")

            # cleanup fields
            cleanup_date_field_names(elem)
            make_aware_dates(elem)

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

    def migrate_user(self, cur):
        """
        Migrate User data
        """
        print("Migrating User...")

        User.objects.filter(api_key__isnull=True).delete()
        reset_app_sql_sequences("users")

        cur.execute("SELECT * FROM user")
        resp = cur.fetchall()
        # print(len(resp))

        # s = set([elem["answer_delay"] for elem in resp])
        # print(s)

        # elem = cur.fetchone()
        # print(elem)

        for elem in resp:
            # rename fields
            rename_field(elem, "enabled", "is_active")
            rename_field(elem, "id", "c4_id")
            rename_field(elem, "phone_prefix", "c4_phone_prefix")
            rename_field(elem, "time_zone", "c4_time_zone")
            rename_field(elem, "website", "c4_website")
            rename_field(elem, "company_name", "c4_company_name")
            rename_field(elem, "siret", "c4_siret")
            rename_field(elem, "naf", "c4_naf")
            rename_field(elem, "phone_verified", "c4_phone_verified")
            rename_field(elem, "email_verified", "c4_email_verified")
            rename_field(elem, "id_card_verified", "c4_id_card_verified")
            rename_field(elem, "accept_survey", "c4_accept_survey")
            rename_field(elem, "accept_rgpd", "c4_accept_rgpd")
            rename_field(elem, "offers_for_pro_sector", "c4_offers_for_pro_sector")
            rename_field(elem, "quote_promise", "c4_quote_promise")

            # cleanup fields
            cleanup_date_field_names(elem)
            make_aware_dates(elem)
            integer_to_boolean(elem)

            # cleanup person_type
            if "person_type" in elem:
                elem["kind"] = map_user_kind(elem["person_type"])

            # set staff users
            if "roles" in elem:
                if elem["roles"].startswith("a:1:{i:0;s:10"):
                    elem["is_staff"] = True
                if elem["roles"].startswith("a:1:{i:0;s:16"):
                    elem["is_superuser"] = True

            # remove useless keys
            [elem.pop(key) for key in USER_EXTRA_KEYS]

            # create object
            # Note: we ignore users with kind=None
            if elem["kind"]:
                try:
                    User.objects.create(**elem)
                except Exception as e:
                    print("a", e)

        print(f"Created {User.objects.count()} users !")

    def migrate_siae_user(self, cur):
        """
        Migrate M2M data between Siae & User

        Notes:
        - elem exemple: {'directory_id': 270, 'user_id': 471234844}
        """
        print("Migrating M2M between Siae & User...")

        Siae.users.through.objects.all().delete()

        cur.execute("SELECT * FROM directory_user")
        resp = cur.fetchall()
        # print(len(resp))
        # print(resp[0])

        for elem in resp:
            try:
                user = User.objects.get(c4_id=elem["user_id"])
                user.siaes.add(elem["directory_id"])
            # Note: some users were ignored because of kind=None. So we ignore the relation as well.
            except:  # noqa
                pass

        print(f"Created {Siae.users.through.objects.count()} M2M objects !")
