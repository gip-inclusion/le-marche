# https://github.com/betagouv/itou/blob/master/itou/utils/apis/api_entreprise.py

import logging

import httpx


logger = logging.getLogger(__name__)


API_ZRR_REASON = "Mise à jour données ZRR du Marché de la plateforme de l'Inclusion"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed

# https://public.opendatasoft.com/explore/dataset/communes-zrr-2017/api/
BASE_URL = "https://public.opendatasoft.com/api/records/1.0/search/"
DATASET_ZRR = "communes-zrr-2017"
DISTANCE_TO_VALIDATE_ZRR = 1000

IS_ZRR_KEY = "is_zrr"
ZRR_NAME_KEY = "ZRR_name"
ZRR_CODE_KEY = "ZRR_code"


def get_default_params():
    return {"dataset": DATASET_ZRR, "refine.zrr_2017": "Classée"}


def get_default_client(params={}):
    params |= get_default_params()
    client = httpx.Client(params=params)
    return client


def is_in_zrr(latitude, longitude, distance=DISTANCE_TO_VALIDATE_ZRR, client=None):
    # API is limited to 5000 calls per day
    # we pass the client to manage the case of many requests
    # client provide default params
    params = {"geofilter.distance": f"{latitude},{longitude},{distance}"}

    if not client:
        client = get_default_client()

    try:
        r = client.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()
        records = data["records"]
        if records:
            zrr = records[0]["fields"]
            return {
                IS_ZRR_KEY: True,
                ZRR_NAME_KEY: zrr["nom_commune"],
                ZRR_CODE_KEY: zrr["com17"],
            }
        return {IS_ZRR_KEY: False}
    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
        raise e
