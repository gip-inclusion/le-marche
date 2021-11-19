from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_entreprise import etablissement_get_or_error, exercice_get_or_error


API_ENTREPRISE_REASON = "Mise à jour donnéés Marché de la plateforme de l'Inclusion"


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py update_api_entreprise_fields
    """

    def handle(self, *args, **options):
        print("-" * 80)
        print("Populating API Entreprise fields...")

        for siae in Siae.objects.all()[:10]:
            self.siae_update_etablissement(siae)
            self.siae_update_exercice(siae)

    def siae_update_etablissement(self, siae):
        etablissement, error = etablissement_get_or_error(siae["siret"], reason=API_ENTREPRISE_REASON)
        if etablissement:
            update_data = dict()
            # update_data"nature"] = Siae.NATURE_HEAD_OFFICE if etablissement["is_head_office"] else Siae.NATURE_ANTENNA  # noqa
            # update_data"is_active"] = False if not etablissement["is_closed"] else True
            update_data["api_entreprise_employees"] = etablissement["employees"]
            update_data["api_entreprise_employees_year_reference"] = etablissement["employees_date_reference"]
            if etablissement["date_constitution"]:
                update_data["api_entreprise_date_constitution"] = timezone.make_aware(
                    etablissement["date_constitution"]
                )
            update_data["api_entreprise_etablissement_last_sync_date"] = timezone.now()
            Siae.objects.filter(id=siae.id).update(**update_data)
        # else:
        #     print(error)
        # TODO: if 404, siret_is_valid = False ?

    def siae_update_exercice(self, siae):
        exercice, error = exercice_get_or_error(siae["siret"], reason=API_ENTREPRISE_REASON)  # noqa
        if exercice:
            update_data = dict()
            update_data["api_entreprise_ca"] = exercice["ca"]
            update_data["api_entreprise_ca_date_fin_exercice"] = exercice[
                "date_fin_exercice"
            ]  # "2016-12-31T00:00:00+01:00"
            update_data["api_entreprise_exercice_last_sync_date"] = timezone.now()
            Siae.objects.filter(id=siae.id).update(**update_data)
        # else:
        #     print(error)
