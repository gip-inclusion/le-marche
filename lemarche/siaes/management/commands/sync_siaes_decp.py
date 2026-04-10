"""
Synchronise le champ `has_won_contract_last_3_years` des SIAEs avec les données
de la commande publique (DECP - data.gouv.fr).

Pour chaque SIAE active avec un SIRET valide, interroge l'API DECP pour vérifier
si la structure a remporté au moins un marché public ces 3 dernières années.

Usage:
    python manage.py sync_siaes_decp
    python manage.py sync_siaes_decp --limit 100   # limiter pour tester
"""

import time
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


DECP_API_URL = "https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/"
DECP_API_TIMEOUT = 10  # secondes
DECP_API_SLEEP_BETWEEN_REQUESTS = 0.05  # 50ms → max ~20 req/s, bien en dessous de la limite de 100 req/s
BATCH_SIZE = getattr(settings, "BATCH_SIZE_BULK_UPDATE", 100)


def has_won_contract(siret: str, date_limit: str) -> bool:
    """
    Interroge l'API DECP pour vérifier si un SIRET a remporté au moins
    un marché public depuis date_limit (format YYYY-MM-DD).
    Retourne True si au moins 1 résultat, False sinon.
    """
    params = {
        "titulaire_id__exact": siret,
        "titulaire_typeIdentifiant__exact": "SIRET",
        "dateNotification__greater": date_limit,
        "page_size": 1,
    }
    response = requests.get(DECP_API_URL, params=params, timeout=DECP_API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return data.get("meta", {}).get("total", 0) > 0


class Command(BaseCommand):
    help = "Synchronise has_won_contract_last_3_years des SIAEs avec les données DECP (data.gouv.fr)"

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
            .filter(siret_is_valid=True)
            .exclude(siret="")
            .only("id", "siret", "has_won_contract_last_3_years")
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
            ]
        )

        siaes_to_update = []
        success_count = 0
        won_count = 0
        error_count = 0
        now = timezone.now()

        for i, siae in enumerate(siaes, 1):
            try:
                result = has_won_contract(siae.siret, date_limit)
                siae.has_won_contract_last_3_years = result
                siae.decp_last_sync_date = now
                siaes_to_update.append(siae)
                success_count += 1
                if result:
                    won_count += 1
            except requests.exceptions.RequestException as e:
                self.stdout_error(f"Erreur SIRET {siae.siret} : {e}")
                error_count += 1

            time.sleep(DECP_API_SLEEP_BETWEEN_REQUESTS)

            if i % 100 == 0:
                self.stdout_info(f"{i}/{total}...")

        Siae.objects.bulk_update(
            siaes_to_update,
            ["has_won_contract_last_3_years", "decp_last_sync_date"],
            batch_size=BATCH_SIZE,
        )

        msg_success = [
            "----- Synchronisation DECP -----",
            f"Traitées : {success_count}/{total}",
            f"Ont remporté un marché ces 3 ans : {won_count}",
            f"Erreurs : {error_count}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
