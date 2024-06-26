from lemarche.perimeters.models import Perimeter
from lemarche.siaes.models import Siae


def calculate_etablissement_count(siae: Siae):
    if siae.siren:
        return Siae.objects.filter(is_active=True, siret__startswith=siae.siren).count()
    return 0


def match_location_to_perimeter(siae: Siae):
    """
    Find the Siae's location based on the post_code (and city)
    - first do a post_code search
    - if multiple perimeters returned, try to match with the city
    - if still multiple results returned, return None
    """
    if siae.post_code:
        location_results_from_siae_post_code = Perimeter.objects.post_code_search(
            siae.post_code, include_insee_code=True
        )

        if not location_results_from_siae_post_code.exists():
            print(f"No location found for {siae} (with post_code {siae.post_code})")
            return None
        elif location_results_from_siae_post_code.count() == 1:
            return location_results_from_siae_post_code.first()
        else:
            # found multiple locations with the post_code, try to match with the city
            if siae.city:
                location_results_from_siae_city = Perimeter.objects.name_search(siae.city)
                if location_results_from_siae_city.count():
                    if location_results_from_siae_post_code.first() == location_results_from_siae_post_code.first():
                        return location_results_from_siae_post_code.first()
                    else:
                        print(f"Multiple locations found for {siae} (with post_code {siae.post_code})")
                        return None
