"""
Synchronise les champs DECP des SIAEs (has_won_contract_last_3_years,
decp_contracts_count_last_3_years, decp_last_sync_date) depuis l'API
publique data.gouv.fr (Données Essentielles de la Commande Publique).

Traite uniquement les SIAEs actives avec un SIRET valide.

Usage:
    python manage.py sync_siaes_decp
    python manage.py sync_siaes_decp --siret 12345678901234
    python manage.py sync_siaes_decp --limit 100
    python manage.py sync_siaes_decp --wet-run
"""

import logging
import time
from datetime import timedelta
from itertools import batched

import requests
from django.utils import timezone
from sentry_sdk.crons import monitor

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_decp, api_slack
from lemarche.utils.commands import BaseCommand


logger = logging.getLogger(__name__)


BATCH_SIZE = 1_000
SLEEP_BETWEEN_REQUESTS = 0.05  # 50 ms → ~20 req/s, bien sous la limite data.gouv.fr


class Command(BaseCommand):
    help = "Synchronise les champs DECP des SIAEs depuis l'API data.gouv.fr"

    def add_arguments(self, parser):
        parser.add_argument("--siret", type=str, default=None, help="Traiter un SIRET spécifique")
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de structures à traiter")
        parser.add_argument("--wet-run", action="store_true", help="Appliquer les changements en base de données")

    @monitor(monitor_slug="sync_siaes_decp")
    def handle(self, *args, **options):
        date_limit = (timezone.now() - timedelta(days=3 * 365)).strftime("%Y-%m-%d")

        if options["siret"]:
            siaes_qs = Siae.objects.filter(siret=options["siret"])
        else:
            siaes_qs = (
                Siae.objects.is_live()
                .filter(siret_is_valid=True)
                .exclude(siret="")
                .only("id", "siret", "has_won_contract_last_3_years", "decp_contracts_count_last_3_years")
                .order_by("id")
            )

        if options["limit"]:
            siaes_qs = siaes_qs[: options["limit"]]

        siaes = list(siaes_qs)
        total = len(siaes)

        self.stdout_messages_info(
            [
                "Synchronisation DECP...",
                f"Date limite : {date_limit}",
                f"{total} SIAEs à traiter",
                "Mode : " + ("wet-run" if options["wet_run"] else "dry-run"),
            ]
        )

        siaes_to_update = []
        success_count = 0
        won_count = 0
        error_count = 0
        now = timezone.now()

        for i, siae in enumerate(siaes, 1):
            try:
                count = api_decp.fetch_contracts_count(siae.siret, date_limit)
                siae.decp_contracts_count_last_3_years = count
                siae.has_won_contract_last_3_years = count > 0
                siae.decp_last_sync_date = now
                siaes_to_update.append(siae)
                success_count += 1
                if count > 0:
                    won_count += 1
            except requests.exceptions.RequestException as e:
                logger.error("Erreur DECP SIRET %s : %s", siae.siret, e)
                error_count += 1

            time.sleep(SLEEP_BETWEEN_REQUESTS)

            if i % 100 == 0:
                self.stdout_info(f"{i}/{total}...")

        if options["wet_run"]:
            for batch in batched(siaes_to_update, BATCH_SIZE):
                objects = list(batch)
                Siae.objects.bulk_update(
                    objects,
                    ["has_won_contract_last_3_years", "decp_contracts_count_last_3_years", "decp_last_sync_date"],
                )

        msg_success = [
            "----- Synchronisation DECP -----",
            f"Traitées : {success_count}/{total}",
            f"Ont remporté un marché ces 3 ans : {won_count}",
            f"Erreurs : {error_count}",
            "Mode : " + ("wet-run (changements appliqués)" if options["wet_run"] else "dry-run (aucun changement)"),
        ]
        self.stdout_messages_success(msg_success)
        if options["wet_run"]:
            api_slack.send_message_to_channel("\n".join(msg_success))
