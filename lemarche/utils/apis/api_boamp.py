import json
import logging

import requests

from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.tenders.models import Tender


logger = logging.getLogger(__name__)


API_ZRR_REASON = "Récolte des données d'appel d'offre BOAMP"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed

# https://boamp-datadila.opendatasoft.com/api/records/1.0/search/?dataset=boamp&q=&rows=10000&sort=dateparution&facet=famille&facet=code_departement&facet=famille_libelle&facet=perimetre&facet=procedure_categorise&facet=nature_categorise_libelle&facet=criteres&facet=marche_public_simplifie&facet=marche_public_simplifie_label&facet=etat&facet=descripteur_code&facet=descripteur_libelle&facet=type_marche&facet=type_marche_facette&facet=type_avis&facet=dateparution&refine.criteres=sociaux&refine.dateparution=2022%2F02
BASE_URL = "https://boamp-datadila.opendatasoft.com/api/records/1.0/search/"


def dump_to_json_file(filename, data):
    with open(f"{filename}.json", "w") as jsonfile:
        json.dump(data, jsonfile)


def get_default_params():
    return {
        "dataset": "boamp",
        "rows": 3000,
        "sort": "dateparution",
        "facet": [
            "famille",
            "famille",
            "code_departement",
            "famille_libelle",
            "perimetre",
            "procedure_categorise",
            "nature_categorise_libelle",
            "criteres",
            "marche_public_simplifie",
            "marche_public_simplifie_label",
            "etat",
            "descripteur_code",
            "descripteur_libelle",
            "type_marche",
            "type_marche_facette",
            "type_avis",
        ],
    }


def get_default_client(params={}):
    params |= get_default_params()
    headers = {
        "user-agent": "betagouv-lemarche/0.0.1",
    }
    client = requests.Session()
    client.params = params
    client.headers = headers

    return client


def get_offers_list(client=None):
    # print(get_offers_list)
    if not client:
        client = get_default_client()

    saved_data = []
    saved_tenders = []
    try:
        # refine.criteres=sociaux
        r = client.get(
            BASE_URL,
            params={
                "refine.dateparution": "2022/09",
                "refine.etat": "INITIAL",
                "refine.nature_categorise_libelle": "Avis de marché",
                "refine.procedure_categorise": "OUVERT",
                "refine.criteres": "sociaux",
            },
        )
        r.raise_for_status()
        data = r.json()
        # add cursor to get all offers if "nbItemsRetournes": 1000 < "nbItemsExistants": 3116
        records = data["records"]
        if records:
            # dump_to_json_file("all_offers", data)
            for offer in records:
                # print(offer)
                offer_saved = offer.get("fields")
                offer_saved |= json.loads(offer_saved.get("donnees", "[]"))
                offer_saved |= json.loads(offer_saved.get("gestion", "[]"))
                offer_saved["annonces_anterieures"] = json.loads(offer_saved.get("annonces_anterieures", "[]"))
                # saved_data.append(offer_saved)
                tender = create_tender_from_record_boamp(offer_saved)
                if tender:
                    saved_data.append(offer_saved)
                    saved_tenders.append(tender)
            # results = Tender.objects.bulk_create(saved_data, batch_size=20)
            print("Nb of tender record", len(saved_tenders))
            print("Nb of tender created", len(saved_tenders))
            dump_to_json_file("offers_saved", saved_data)
            return saved_data

    except requests.exceptions.HTTPError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)


def create_tender_from_record_boamp(record: dict) -> Tender:
    identity_tender = record.get("IDENTITE")
    object_tender = record.get("OBJET", {})
    cpv_code = object_tender.get("CPV", {})
    sectors = get_sectors_from_cpv(cpv_code)
    perimeters = Perimeter.objects.filter(
        post_codes__contains=[record.get("IDENTITE").get("CP")]
    )  # add regions in the future
    if perimeters:
        title = extract_max_field(object_tender.get("TITRE_MARCHE", ""))
        desciption = extract_max_field(object_tender.get("OBJET_COMPLET", ""))
        constraints = extract_max_field(record.get("CONDITION_PARTICIPATION", ""))
        external_link = extract_max_field(
            identity_tender.get("URL_DOCUMENT") or identity_tender.get("URL_PROFIL_ACHETEUR") or ""
        )
        tender = Tender(
            title=title,
            kind=Tender.TENDER_KIND_BOAMP,
            description=desciption,
            constraints=constraints,
            external_link=external_link,
            deadline_date=record.get("datefindiffusion"),
            response_kind=[Tender.RESPONSE_KIND_EXTERNAL],
            contact_first_name=identity_tender.get("DENOMINATION"),
            contact_last_name=identity_tender.get("CONTACT", ""),
            contact_email=identity_tender.get("MEL", ""),
            contact_phone=identity_tender.get("TEL", "").replace(" ", "").replace("-", ""),
            # sectors=sectors,
            # perimeters=perimeters,
            is_country_area=False,
            presta_type=siae_constants.PRESTA_CHOICES,  # type de prestation, utiliser decripteur_libelle
            author=None,  # need to precise it ?
            accept_share_amount=False,
        )

        tender.save()
        tender.sectors.set(sectors)
        tender.perimeters.set(perimeters)
        print("Created tender : ", tender)
        return tender


def extract_max_field(field: str, max_length=255):
    item = field if len(field) <= 255 else field[:max_length]
    return item


def get_sectors_from_cpv(cpv_code):
    if cpv_code and type(cpv_code) == list:
        cpv_codes = [cpv_code_item.get("PRINCIPAL") for cpv_code_item in cpv_code]
        sectors = Sector.objects.prefetch_related("cpv_codes").filter(cpv_codes__in=cpv_codes)
    elif cpv_code:
        cpv_code = cpv_code.get("PRINCIPAL")
        sectors = Sector.objects.prefetch_related("cpv_codes").filter(cpv_codes=cpv_code)
    else:
        sectors = Sector.objects.none()
    return sectors
