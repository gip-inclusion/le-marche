import requests


DECP_API_URL = "https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/"
DECP_API_TIMEOUT = 10


def fetch_contracts_count(siret: str, date_limit: str) -> int:
    """
    Retourne le nombre de marchés remportés par un SIRET depuis date_limit (YYYY-MM-DD).
    Retourne 0 en cas d'absence de données.
    Lève requests.exceptions.RequestException en cas d'erreur réseau ou HTTP.
    """
    params = {
        "titulaire_id__exact": siret,
        "titulaire_typeIdentifiant__exact": "SIRET",
        "dateNotification__greater": date_limit,
        "page_size": 1,
    }
    response = requests.get(DECP_API_URL, params=params, timeout=DECP_API_TIMEOUT)
    response.raise_for_status()
    return response.json().get("meta", {}).get("total", 0)


def fetch_recent_contracts(siret: str, date_limit: str, max_results: int = 50) -> list[dict]:
    """
    Retourne les marchés remportés par un SIRET depuis date_limit, triés du plus récent au plus ancien.
    Filtre sur donneesActuelles=true (version courante du marché uniquement).
    Lève requests.exceptions.RequestException en cas d'erreur réseau ou HTTP.
    """
    params = {
        "titulaire_id__exact": siret,
        "titulaire_typeIdentifiant__exact": "SIRET",
        "donneesActuelles__exact": "true",
        "dateNotification__greater": date_limit,
        "dateNotification__sort": "desc",
        "page_size": max_results,
    }
    response = requests.get(DECP_API_URL, params=params, timeout=DECP_API_TIMEOUT)
    response.raise_for_status()
    return response.json().get("data", [])
