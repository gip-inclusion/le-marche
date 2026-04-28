import requests


DECP_API_URL = "https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/"
DECP_API_TIMEOUT = 10


def _get(params: dict) -> dict:
    response = requests.get(DECP_API_URL, params=params, timeout=DECP_API_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_contracts_count(siret: str, date_limit: str) -> int:
    """
    Retourne le nombre de marchés remportés par un SIRET depuis date_limit (YYYY-MM-DD).
    Essaie d'abord le SIRET exact, puis le SIREN (9 premiers chiffres) en fallback
    pour couvrir les contrats attribués à d'autres établissements du même groupe.
    Retourne 0 en cas d'absence de données.
    Lève requests.exceptions.RequestException en cas d'erreur réseau ou HTTP.
    """
    base_params = {"dateNotification__greater": date_limit, "page_size": 1}

    data = _get({**base_params, "titulaire_id__exact": siret, "titulaire_typeIdentifiant__exact": "SIRET"})
    count = data.get("meta", {}).get("total", 0)
    if count > 0:
        return count

    # Fallback SIREN : couvre les autres établissements du même groupe
    siren = siret[:9]
    data = _get({**base_params, "titulaire_id__contains": siren})
    return data.get("meta", {}).get("total", 0)


def fetch_recent_contracts(siret: str, date_limit: str, max_results: int = 50) -> list[dict]:
    """
    Retourne les marchés remportés par un SIRET depuis date_limit, triés du plus récent au plus ancien.
    Filtre sur donneesActuelles=true (version courante du marché uniquement).
    Essaie d'abord le SIRET exact, puis le SIREN en fallback.
    Lève requests.exceptions.RequestException en cas d'erreur réseau ou HTTP.
    """
    base_params = {
        "donneesActuelles__exact": "true",
        "dateNotification__greater": date_limit,
        "dateNotification__sort": "desc",
        "page_size": max_results,
    }

    data = _get({**base_params, "titulaire_id__exact": siret, "titulaire_typeIdentifiant__exact": "SIRET"})
    rows = data.get("data", [])
    if rows:
        return rows

    # Fallback SIREN : couvre les autres établissements du même groupe
    siren = siret[:9]
    data = _get({**base_params, "titulaire_id__contains": siren})
    return data.get("data", [])
