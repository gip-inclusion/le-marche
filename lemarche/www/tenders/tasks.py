from huey.contrib.djhuey import task

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender


@task()
def find_opportunities_for_siaes(tender: Tender):
    """Function to find new opportunities from the tender

    Args:
        tender (tenders.Tender): Need of the buyer
    """
    siaes_potentially_interested = (
        Siae.objects.is_live()
        .prefetch_many_to_many()
        .in_cities_area(tender.perimeters.all())
        .filter_sectors(tender.sectors.all())
    )

    for siae in siaes_potentially_interested:
        print(siae)
