import logging
from datetime import datetime
from xml.etree import ElementTree

import requests


logger = logging.getLogger(__name__)


INFO_URL = "https://www.maximilien.fr/"
BASE_URL = "https://marches.maximilien.fr/rssCS.xml"
# Example? api_marche_maximilien_example.txt
# FIELD_MAPPING = {
#     "title": "title",
#     "description": "description",
#     "external_link": "link",
#     "created_at": "pubDate"
# }
TIMESTAMP_FORMAT = "%a, %d %b %Y %H:%M:%S %z"  # Wed, 05 Oct 2022 14:00:00 +0200


def get_default_params():
    return {}


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
    if not client:
        client = get_default_client()

    offer_list = []

    try:
        r = client.get(BASE_URL)
        r.raise_for_status()

        tree = ElementTree.fromstring(r.content)
        print(tree)
        print(tree.find("channel"))  # title, link, description, pubDate, lastBuildDate, ttl, language, item(s)
        print(len(tree.find("channel").findall("item")))

        for item in tree.find("channel").findall("item"):
            offer = {}

            # TODO: finish field mapping
            # basics
            offer["title"] = item.find("title").text
            offer["description"] = item.find("description").text
            offer["external_link"] = item.find("title").text
            offer["created_at"] = datetime.strptime(item.find("pubDate").text, TIMESTAMP_FORMAT)
            # offer["source"] = "MAXIMILIEN"
            # offer["source_id"] = item.find("guid").split("_")[0]

            # category : Avis, Titre, Objet, Procedure, DateLimite, DateOuverture, Category, Organisme, Organisme_nom, Organisme_siren, Organisme_code_postal, EntiteAchat, LieuxExecution, ClosureDate, cpv, Lot  # noqa
            # - Titre: same as title
            # - Organisme_nom: author
            # - ClosureDate: difference with DateLimite?
            # - LieuxExecution: comma-seperated departments
            # - cpv: comma-seperated codes
            # - Lot: not always present ; multiple entries
            offer["deadline_date"] = datetime.strptime(
                item.find("category/[@domain='DateLimite']").text, TIMESTAMP_FORMAT
            ).date()

            # filter on inclusion?
            # "clause d'insertion" ; "réservé à une structure d'insertion" ; "SIAE" ; "entreprises adaptées" ; "entreprise adaptée"  # noqa
            offer_list.append(offer)

    except requests.exceptions.HTTPError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
