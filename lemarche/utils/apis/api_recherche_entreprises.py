from dataclasses import dataclass
from datetime import date

import requests
from django.conf import settings


# https://sirene.fr/static-resources/htm/v_sommaire_311.htm#27
TRANCHES_EFFECTIF_SALARIE_MAPPING = {
    "NN": "Etablissement non-employeur",
    "00": "0 salarié",
    "01": "1 ou 2 salariés",
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1 000 à 1 999 salariés",
    "51": "2 000 à 4 999 salariés",
    "52": "5 000 à 9 999 salariés",
    "53": "10 000 salariés et plus",
}


@dataclass
class RechercheEntreprisesResponse:
    siret: str
    forme_juridique_code: str
    date_creation: date
    naf: str
    is_closed: bool
    is_head_office: bool
    employees: str
    employees_date_reference: date
    ca: str | None
    ca_date_reference: date | None


def recherche_entreprises_get_or_error(siret):
    # Doc : https://recherche-entreprises.api.gouv.fr/docs/
    url = f"{settings.API_RECHERCHE_ENTREPRISES_BASE_URL}/search?q={siret}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        response_data = response.json()

        if response_data["total_results"] == 0:
            return None, "SIRET not found"
        elif response_data["total_results"] > 1:
            return None, "SIRET found but multiple results"
        else:
            # get interesting data
            data = response_data["results"][0]

            ca = None
            ca_date_reference = None
            if "finances" in data and data["finances"]:
                finances = data["finances"]
                # Sort the finances data by year in descending order
                sorted_finances = sorted(finances.items(), key=lambda x: x[0], reverse=True)
                ca_date_reference = sorted_finances[0][0]
                ca = sorted_finances[0][1]["ca"]

            etablissement = data["matching_etablissements"][0]
            return (
                RechercheEntreprisesResponse(
                    siret=etablissement["siret"],
                    forme_juridique_code=data["nature_juridique"],
                    date_creation=etablissement["date_creation"],
                    naf=etablissement["activite_principale"],
                    is_closed=etablissement["etat_administratif"] == "F",
                    is_head_office=etablissement["est_siege"],
                    employees=TRANCHES_EFFECTIF_SALARIE_MAPPING.get(etablissement["tranche_effectif_salarie"], ""),
                    employees_date_reference=etablissement["annee_tranche_effectif_salarie"],
                    ca=ca,
                    ca_date_reference=ca_date_reference,
                ),
                None,
            )

    except requests.exceptions.HTTPError as e:
        return None, f"Error while fetching `{url}`: {e}"
