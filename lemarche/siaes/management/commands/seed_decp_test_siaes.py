"""
Prépare des SIAEs de test pour valider la synchronisation DECP en environnement
de recette. Marque un échantillon de SIAEs comme ayant un SIRET valide afin qu'elles
soient traitées par sync_siaes_decp.

À lancer sur la recette uniquement, avant sync_siaes_decp.

Usage:
    python manage.py seed_decp_test_siaes
    python manage.py seed_decp_test_siaes --count 20
"""

from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


SIRET_LENGTH = 14


class Command(BaseCommand):
    help = "Marque un échantillon de SIAEs comme siret_is_valid=True pour tester sync_siaes_decp en recette"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=10, help="Nombre de SIAEs à marquer comme valides (défaut : 10)"
        )

    def handle(self, *args, **options):
        count = options["count"]

        siaes = (
            Siae.objects.filter(is_active=True, siret_is_valid__in=[False, None])
            .exclude(siret="")
            .extra(where=["LENGTH(siret) = 14"])
            .order_by("id")[:count]
        )
        siaes = list(siaes)

        if not siaes:
            self.stdout_error("Aucune SIAE trouvée avec un SIRET de 14 chiffres et siret_is_valid=None.")
            return

        for siae in siaes:
            siae.siret_is_valid = True

        Siae.objects.bulk_update(siaes, ["siret_is_valid"])

        self.stdout_messages_success(
            [
                f"{len(siaes)} SIAEs marquées siret_is_valid=True :",
                *[f"  {s.siret} — {s.name}" for s in siaes],
                "",
                "Vous pouvez maintenant lancer :",
                f"  python manage.py sync_siaes_decp --limit {len(siaes)} --wet-run",
                "  python manage.py sync_siaes_decp_details --wet-run",
            ]
        )
