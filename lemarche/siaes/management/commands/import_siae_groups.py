import csv
import os

from django.core.management.base import BaseCommand

from lemarche.siaes.models import SiaeGroup
from lemarche.utils.data import rename_dict_key, reset_app_sql_sequences


SIAE_GROUP_FIELDS = [field.name for field in SiaeGroup._meta.fields]
FILE_NAME = "siaegroups.csv"
FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME


def read_csv(file_path):
    siae_group_list = list()

    with open(file_path) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):

            siae_group_list.append(row)

    return siae_group_list


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py import_siae_groups
    """

    def handle(self, *args, **options):
        print("-" * 80)
        SiaeGroup.objects.all().delete()
        reset_app_sql_sequences("siaes")

        print("Importing Siae Groups...")
        siae_group_list = read_csv(FILE_PATH)
        progress = 0
        for index, siae_group in enumerate(siae_group_list):
            progress += 1
            if (progress % 10) == 0:
                print(f"{progress}...")
            self.import_siae_groups(siae_group)

        print("Done !")
        print(f"Imported {SiaeGroup.objects.count()} Siae Groups")

    def import_siae_groups(self, siae_group):  # noqa C901
        # store raw dict
        # siae["import_raw_object"] = siae_group.copy()

        # basic fields
        rename_dict_key(siae_group, "Quel est le nom de votre groupement ?", "name")
        siae_group["name"].strip()
        rename_dict_key(siae_group, "Quel est le numéro de SIRET de votre groupement ?", "siret")
        if "siret" in siae_group:
            siae_group["siret"].strip()
            siae_group["siret"] = siae_group["siret"].replace(" ", "").replace(" ", "")

        # contact fields
        # rename_dict_key(siae_group, "Prénom 1", "contact_first_name")
        # rename_dict_key(siae_group, "Nom 1", "contact_last_name")
        rename_dict_key(siae_group, "Quel est votre site internet ?", "contact_website")
        rename_dict_key(siae_group, "Quelle est votre adresse email ?", "contact_email")
        rename_dict_key(siae_group, "Quel est votre numéro de téléphone ?", "contact_phone")

        # other fields
        rename_dict_key(siae_group, "Combien de structures composent votre groupement ?", "siae_count")
        siae_group["siae_count"] = siae_group["siae_count"] if siae_group["siae_count"].isnumeric() else None
        rename_dict_key(
            siae_group, "Combien de salariés en insertion composent votre réseau ?", "employees_insertion_count"
        )
        siae_group["employees_insertion_count"] = (
            siae_group["employees_insertion_count"] if siae_group["employees_insertion_count"].isnumeric() else None
        )
        rename_dict_key(
            siae_group, "Combien de salariés permanents composent votre groupement ?", "employees_permanent_count"
        )
        siae_group["employees_permanent_count"] = (
            siae_group["employees_permanent_count"] if siae_group["employees_permanent_count"].isnumeric() else None
        )
        rename_dict_key(siae_group, "Quel est le chiffre d'affaires annuel de votre groupement ?", "ca")
        siae_group["ca"] = siae_group["ca"] if siae_group["ca"].isnumeric() else None
        rename_dict_key(siae_group, "Glissez ici le logo de votre groupement.", "logo_url")

        # cleanup unused fields
        siae_group_cleaned = dict()
        for key in siae_group:
            if key in SIAE_GROUP_FIELDS:
                siae_group_cleaned[key] = siae_group[key]

        # create object
        try:
            SiaeGroup.objects.create(**siae_group_cleaned)
        except Exception as e:
            print(e)
            print(siae_group_cleaned)
