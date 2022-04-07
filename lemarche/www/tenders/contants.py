from django.db.models import Q

from lemarche.tenders.models import Tender


""" Constants for tenders:
- Filters when send tenders for our parteners
"""


FILTER_KIND_AMOUNT = "amount"
FILTER_KIND_COMPANY = "company"
FILTER_KIND_PERIMETERS = "perimeters"

PARTNER_FILTERS = [
    {
        "name": "Linklusion",
        "filter_kind": [],
        "contacts_email": ["jalil@linklusion.fr"],
    },
    {
        "name": "Adie",
        "filter_kind": [FILTER_KIND_AMOUNT],
        "amount_in": (Tender.AMOUNT_RANGE_0, Tender.AMOUNT_RANGE_1),
        "contacts_email": ["csaintaurens@adie.org", "phenric@adie.org"],
    },
    {
        "name": "Handeco",
        "filter_kind": [],
        "contacts_email": ["joseph.ramos@handeco.org"],
    },
    {
        "name": "Réseau Gesat",
        "filter_kind": [],
        "contacts_email": ["denis.charrier@reseau-gesat.com"],
    },
    {
        "name": "IRIAE HDF",
        "filter_kind": [FILTER_KIND_PERIMETERS],
        "perimeters_filter": Q(name="Hauts-de-France") | Q(region_code="32"),
        "contacts_email": ["iluu@iriaehdf.com"],
    },
    {
        "name": "URSIAE",
        "filter_kind": [FILTER_KIND_PERIMETERS],
        "perimeters_filter": Q(name="La Réunion") | Q(region_code="04"),
        "contacts_email": ["developpement.ursiae974@gmail.com"],
    },
    {
        "name": "URSIAE",
        # Grand Est
        "filter_kind": [FILTER_KIND_PERIMETERS],
        "perimeters_filter": Q(name="Grand Est"),
        "contacts_email": ["emmanuelle.daviau@ursiea.org"],
    },
]
