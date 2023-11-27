import requests
from django.conf import settings


API_ENDPOINT = f"{settings.API_EMPLOIS_INCLUSION_URL}/marche"
API_HEADERS = {"Authorization": f"Token {settings.API_EMPLOIS_INCLUSION_TOKEN}"}


def get_siae_list():
    siae_list = list()
    pagination = 0

    # loop on API to fetch all the data
    while True:
        response = requests.get(f"{API_ENDPOINT}?page_size={pagination}", headers=API_HEADERS)
        data = response.json()
        if data["results"]:
            for siae in data["results"]:
                siae_list.append(siae)
        if data["next"]:
            pagination += 1000
        else:
            break

    return siae_list
