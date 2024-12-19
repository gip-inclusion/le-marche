import time
from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from sentry_sdk.crons import monitor

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.apis.api_entreprise import (
    API_ENTREPRISE_REASON,
    entreprise_get_or_error,
    etablissement_get_or_error,
    exercice_get_or_error,
)
from lemarche.utils.commands import BaseCommand


SCOPE_ALLOWED_VALUES = ("all", "entreprise", "etablissement", "exercice")


class Command(BaseCommand):
    """
    Populates API Entreprise fields

    Note: Only on Siae who have api_entreprise_*_last_sync_date as None

    TODO: filter only on Siae not updated since a certain date?

    Usage:
    - poetry run python manage.py update_api_entreprise_fields
    - poetry run python manage.py update_api_entreprise_fields --scope etablissement
    - poetry run python manage.py update_api_entreprise_fields --siret 01234567891011
    - poetry run python manage.py update_api_entreprise_fields --limit 100
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--scope", type=str, default="all", help="Options are 'entreprise', 'etablissement', 'exercice', or 'all'"
        )
        parser.add_argument("--siret", type=str, default=None, help="Lancer sur un Siret spécifique")
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de structures à processer")

    @monitor(monitor_slug="update-api-entreprise-fields")
    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Populating API Entreprise fields...")

        if options["scope"] not in SCOPE_ALLOWED_VALUES:
            raise Exception(f"scope not in {SCOPE_ALLOWED_VALUES}")

        if options["siret"]:
            siae_queryset = Siae.objects.filter(siret=options["siret"])
        else:
            siae_queryset = Siae.objects.filter(
                Q(api_entreprise_entreprise_last_sync_date=None)
                | Q(api_entreprise_etablissement_last_sync_date=None)
                | Q(api_entreprise_exercice_last_sync_date=None)
            ).order_by("id")

        if options["limit"]:
            siae_queryset = siae_queryset[: options["limit"]]

        self._update_siae_api_entreprise_fields(siae_queryset, options["scope"])

    def _update_siae_api_entreprise_fields(self, siae_queryset, scope):
        results = {
            "entreprise": {"success": 0, "error": 0},
            "etablissement": {"success": 0, "error": 0},
            "exercice": {"success": 0, "error": 0},
        }

        progress = 0
        for siae in siae_queryset:
            progress += 1
            if (progress % 50) == 0:
                self.stdout_info(f"{progress}...")

            if not siae.siret:
                self.stdout_error(f"SIAE {siae.id} without SIRET")
                continue

            update_data = dict()
            if scope in ("all", "entreprise") and siae.api_entreprise_entreprise_last_sync_date is None:
                entreprise, error = entreprise_get_or_error(siae.siret[:9], reason=API_ENTREPRISE_REASON)
                if error:
                    results["entreprise"]["error"] += 1
                    self.stdout_error(str(error))
                else:
                    results["entreprise"]["success"] += 1
                    update_data["api_entreprise_forme_juridique"] = entreprise.forme_juridique
                    update_data["api_entreprise_forme_juridique_code"] = entreprise.forme_juridique_code
                    update_data["api_entreprise_entreprise_last_sync_date"] = timezone.now()

            if scope in ("all", "etablissement") and siae.api_entreprise_etablissement_last_sync_date is None:
                etablissement, error = etablissement_get_or_error(siae.siret, reason=API_ENTREPRISE_REASON)
                if error:
                    results["etablissement"]["error"] += 1
                    self.stdout_error(str(error))
                else:
                    results["etablissement"]["success"] += 1
                    update_data["api_entreprise_employees"] = (
                        etablissement.employees
                        if (etablissement.employees != "Unités non employeuses")
                        else "Non renseigné"
                    )
                    update_data["api_entreprise_employees_year_reference"] = etablissement.employees_date_reference
                    update_data["api_entreprise_date_constitution"] = etablissement.date_constitution
                    update_data["api_entreprise_etablissement_last_sync_date"] = timezone.now()

            if scope in ("all", "exercice") and siae.api_entreprise_exercice_last_sync_date is None:
                exercice, error = exercice_get_or_error(siae.siret, reason=API_ENTREPRISE_REASON)
                if error:
                    results["exercice"]["error"] += 1
                    self.stdout_error(str(error))
                else:
                    results["exercice"]["success"] += 1
                    update_data["api_entreprise_ca"] = exercice.chiffre_affaires
                    update_data["api_entreprise_ca_date_fin_exercice"] = datetime.strptime(
                        exercice.date_fin_exercice, "%Y-%m-%d"
                    ).date()
                    update_data["api_entreprise_exercice_last_sync_date"] = timezone.now()

            Siae.objects.filter(id=siae.id).update(**update_data)

            # small delay to avoid going above the API limitation, one loop generates 3 requests
            # "max. 250 requêtes/min/jeton cumulées sur tous les endpoints"
            time.sleep(1)

        msg_success = [
            "----- Synchronisation API Entreprise -----",
            f"Done! Processed {siae_queryset.count()} siae",
            "----- Success -----",
            f"entreprise: {results['entreprise']['success']}/{siae_queryset.count()}",
            f"etablissement: {results['etablissement']['success']}/{siae_queryset.count()}",
            f"exercice: {results['exercice']['success']}/{siae_queryset.count()}",
            "----- Error ----- (voir les logs)",
            f"entreprise: {results['entreprise']['error']}/{siae_queryset.count()}",
            f"etablissement: {results['etablissement']['error']}/{siae_queryset.count()}",
            f"exercice: {results['exercice']['error']}/{siae_queryset.count()}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
