import csv

from django.db.models import Q

from lemarche.perimeters.models import Perimeter
from lemarche.tenders.models import PartnerShareTender


def run():
    """
    This script is used to import a list of partners from a csv
    To use it, get the csv list and call it list_partners_share_tenders.csv"
    how to use it :
        ./manage.py runscript import_partners_tender
    """
    file_to_read = "list_partners_share_tenders.csv"
    with open(file_to_read) as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        for row in reader:
            print(row)
            name, _, _, email, perimeter_name, _, _ = row

            partner = PartnerShareTender.objects.filter(name=name)
            partner_exist = partner.count() > 0
            if not partner_exist and perimeter_name and perimeter_name != "France entière":
                partner = PartnerShareTender(name=name, contact_email_list=[email])
                partner.save()
                perimeters = Perimeter.objects.filter(name=perimeter_name).distinct()
                conditions = Q(name=perimeter_name)
                for perimeter in perimeters:
                    if perimeter.kind == Perimeter.KIND_REGION:
                        conditions |= Q(region_code=perimeter.insee_code[1:])
                if conditions != Q(name=perimeter_name):
                    perimeters = Perimeter.objects.filter(conditions).distinct()

                if perimeters:
                    print(f"Ajout de {len(perimeters)} perimeters")
                    partner.perimeters.add(*perimeters)
            else:
                if partner_exist:
                    partner[0].contact_email_list.append(email)
                    partner[0].save()
