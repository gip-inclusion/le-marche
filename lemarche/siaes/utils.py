from lemarche.siaes.models import Siae


def calculate_etablissement_count(siae: Siae):
    if siae.siren:
        return Siae.objects.filter(is_active=True, siret__startswith=siae.siren).count()
    return 0
