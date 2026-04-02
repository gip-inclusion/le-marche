"""
Synchronise les détails des marchés publics remportés par chaque SIAE
depuis les DECP (data.gouv.fr), et stocke les 3 derniers marchés uniques
dans la table SiaePublicMarket.

Ne traite que les SIAEs ayant déjà has_won_contract_last_3_years=True
(calculé par sync_siaes_decp).

Usage:
    python manage.py sync_siaes_decp_details
    python manage.py sync_siaes_decp_details --limit 10   # pour tester
"""

import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone

from lemarche.siaes.models import Siae, SiaePublicMarket
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


DECP_API_URL = "https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/"
DECP_API_TIMEOUT = 10
DECP_API_SLEEP_BETWEEN_REQUESTS = 0.05  # 50ms → ~20 req/s, bien en dessous de la limite


def fetch_last_markets(siret: str, date_limit: str) -> list[dict]:
    """
    Interroge l'API DECP pour un SIRET donné.
    Retourne au maximum 3 marchés uniques (dédupliqués par uid),
    triés du plus récent au plus ancien.
    Les lignes sans acheteur_nom ou sans objet sont ignorées.
    """
    params = {
        "titulaire_id__exact": siret,
        "titulaire_typeIdentifiant__exact": "SIRET",
        "donneesActuelles__exact": "true",
        "dateNotification__greater": date_limit,
        "dateNotification__sort": "desc",
        "page_size": 50,
    }
    response = requests.get(DECP_API_URL, params=params, timeout=DECP_API_TIMEOUT)
    response.raise_for_status()
    rows = response.json().get("data", [])

    seen_uids: set[str] = set()
    unique_markets: list[dict] = []
    for row in rows:
        uid = row.get("uid")
        if not uid or uid in seen_uids:
            continue
        if not row.get("acheteur_nom") or not row.get("objet"):
            continue
        seen_uids.add(uid)
        unique_markets.append(row)
        if len(unique_markets) == 3:
            break

    return unique_markets


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def parse_amount(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


class Command(BaseCommand):
    help = "Synchronise les détails des marchés publics remportés des SIAEs (DECP - data.gouv.fr)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limiter le nombre de structures à traiter (utile pour les tests)",
        )

    def handle(self, *args, **options):
        date_limit = (timezone.now() - timedelta(days=3 * 365)).strftime("%Y-%m-%d")

        siaes_qs = (
            Siae.objects.is_live()
            .filter(siret_is_valid=True, has_won_contract_last_3_years=True)
            .exclude(siret="")
            .only("id", "siret")
            .order_by("id")
        )

        if options["limit"]:
            siaes_qs = siaes_qs[: options["limit"]]

        siaes = list(siaes_qs)
        total = len(siaes)

        self.stdout_messages_info([
            "Synchronisation des détails DECP...",
            f"Date limite : {date_limit}",
            f"{total} SIAEs à traiter",
        ])

        success_count = 0
        created_count = 0
        error_count = 0

        for i, siae in enumerate(siaes, 1):
            try:
                markets = fetch_last_markets(siae.siret, date_limit)

                SiaePublicMarket.objects.filter(siae=siae).delete()

                for row in markets:
                    date_notification = parse_date(row.get("dateNotification"))
                    date_publication = parse_date(row.get("datePublicationDonnees"))

                    if date_notification:
                        award_date = date_notification
                        source_date_type = "dateNotification"
                    else:
                        award_date = date_publication
                        source_date_type = "datePublicationDonnees"

                    SiaePublicMarket.objects.create(
                        siae=siae,
                        market_uid=row.get("uid", ""),
                        buyer_name=row.get("acheteur_nom", "")[:500],
                        market_object=row.get("objet", ""),
                        amount=parse_amount(row.get("montant")),
                        award_date=award_date,
                        source_date_type=source_date_type,
                    )
                    created_count += 1

                success_count += 1
            except requests.exceptions.RequestException as e:
                self.stdout_error(f"Erreur SIRET {siae.siret} : {e}")
                error_count += 1

            time.sleep(DECP_API_SLEEP_BETWEEN_REQUESTS)

            if i % 100 == 0:
                self.stdout_info(f"{i}/{total}...")

        msg_success = [
            "----- Synchronisation détails DECP -----",
            f"Traitées : {success_count}/{total}",
            f"Marchés stockés : {created_count}",
            f"Erreurs : {error_count}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
