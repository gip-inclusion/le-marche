"""
Stocke les 3 derniers marchés publics remportés (source DECP) pour chaque SIAE
ayant has_won_contract_last_3_years=True dans la table SiaePublicMarket.

Doit être lancée après sync_siaes_decp.

Usage:
    python manage.py sync_siaes_decp_details
    python manage.py sync_siaes_decp_details --siret 12345678901234
    python manage.py sync_siaes_decp_details --limit 10
    python manage.py sync_siaes_decp_details --wet-run
"""

import logging
import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone
from sentry_sdk.crons import monitor

from lemarche.siaes.models import Siae, SiaePublicMarket
from lemarche.utils.apis import api_decp, api_slack
from lemarche.utils.commands import BaseCommand


logger = logging.getLogger(__name__)

MAX_MARKETS_PER_SIAE = 3
SLEEP_BETWEEN_REQUESTS = 0.05  # 50 ms → ~20 req/s


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _parse_amount(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _select_unique_markets(rows: list[dict]) -> list[dict]:
    """
    Déduplique par uid et filtre les lignes sans acheteur ni objet.
    Retourne au maximum MAX_MARKETS_PER_SIAE marchés.
    """
    seen_uids: set[str] = set()
    result: list[dict] = []
    for row in rows:
        uid = row.get("uid")
        if not uid or uid in seen_uids:
            continue
        if not row.get("acheteur_nom") or not row.get("objet"):
            continue
        seen_uids.add(uid)
        result.append(row)
        if len(result) == MAX_MARKETS_PER_SIAE:
            break
    return result


class Command(BaseCommand):
    help = "Synchronise les détails des marchés publics remportés (DECP) dans SiaePublicMarket"

    def add_arguments(self, parser):
        parser.add_argument("--siret", type=str, default=None, help="Traiter un SIRET spécifique")
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de structures à traiter")
        parser.add_argument("--wet-run", action="store_true", help="Appliquer les changements en base de données")

    @monitor(monitor_slug="sync_siaes_decp_details")
    def handle(self, *args, **options):
        date_limit = (timezone.now() - timedelta(days=3 * 365)).strftime("%Y-%m-%d")

        if options["siret"]:
            siaes_qs = Siae.objects.filter(siret=options["siret"])
        else:
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

        self.stdout_messages_info(
            [
                "Synchronisation des détails DECP...",
                f"Date limite : {date_limit}",
                f"{total} SIAEs à traiter",
                "Mode : " + ("wet-run" if options["wet_run"] else "dry-run"),
            ]
        )

        success_count = 0
        created_count = 0
        error_count = 0

        for i, siae in enumerate(siaes, 1):
            try:
                rows = api_decp.fetch_recent_contracts(siae.siret, date_limit)
                markets = _select_unique_markets(rows)

                if options["wet_run"]:
                    SiaePublicMarket.objects.filter(siae=siae).delete()
                    for row in markets:
                        date_notification = _parse_date(row.get("dateNotification"))
                        date_publication = _parse_date(row.get("datePublicationDonnees"))

                        if date_notification:
                            award_date = date_notification
                            source_date_type = SiaePublicMarket.SOURCE_DATE_NOTIFICATION
                        else:
                            award_date = date_publication
                            source_date_type = SiaePublicMarket.SOURCE_DATE_PUBLICATION

                        SiaePublicMarket.objects.create(
                            siae=siae,
                            market_uid=row.get("uid", ""),
                            buyer_name=(row.get("acheteur_nom") or "")[:500],
                            market_object=row.get("objet") or "",
                            amount=_parse_amount(row.get("montant")),
                            award_date=award_date,
                            source_date_type=source_date_type,
                            cpv_code=(row.get("codeCPV") or "")[:20],
                            procedure_type=(row.get("procedure") or "")[:100],
                            lieu_execution=(row.get("lieuExecution_nom") or "")[:200],
                        )
                        created_count += 1

                success_count += 1
            except requests.exceptions.RequestException as e:
                logger.error("Erreur DECP détails SIRET %s : %s", siae.siret, e)
                error_count += 1

            time.sleep(SLEEP_BETWEEN_REQUESTS)

            if i % 100 == 0:
                self.stdout_info(f"{i}/{total}...")

        msg_success = [
            "----- Synchronisation détails DECP -----",
            f"Traitées : {success_count}/{total}",
            f"Marchés stockés : {created_count}",
            f"Erreurs : {error_count}",
            "Mode : " + ("wet-run (changements appliqués)" if options["wet_run"] else "dry-run (aucun changement)"),
        ]
        self.stdout_messages_success(msg_success)
        if options["wet_run"]:
            api_slack.send_message_to_channel("\n".join(msg_success))
