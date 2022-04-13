from django.db.models import Q

from lemarche.tenders.models import Tender


""" Constants for tenders:
- Filters when send tenders for our parteners
"""


def match_tender_for_partners(tender: Tender, send_email_func=None):
    """Manage the matching from tender to partners

    Args:
        tender (Tender): _description_
        send_email_func : function which takes two arguments tender, and dict of partner (see PARTNERS_FILTERS)

    Returns:
        list<Dict>: list of partners
    """
    partner_list_insterested = []
    for partner in PARTNER_FILTERS:
        send_email = True

        if FILTER_KIND_AMOUNT in partner.get("filter_kind"):
            send_email = tender.amount in partner.get(FILTER_KIND_AMOUNT)

        if FILTER_KIND_PERIMETERS in partner.get("filter_kind") and send_email:
            send_email = tender.perimeters.filter(partner.get(FILTER_KIND_PERIMETERS)).exists()

        if send_email:
            partner_list_insterested.append(partner)
            if send_email_func:
                # avoid circular import
                # + more modular, can use diffrents functions to send email
                send_email_func(tender, partner)

    return partner_list_insterested


FILTER_KIND_AMOUNT = "amount_in"
FILTER_KIND_COMPANY = "company"
FILTER_KIND_PERIMETERS = "perimeters"

PARTNER_FILTERS = [
    {
        "name": "Linklusion",
        "contacts_email": ["jalil@linklusion.fr"],
        "filter_kind": [],
    },
    {
        "name": "Adie",
        "contacts_email": ["csaintaurens@adie.org", "phenric@adie.org"],
        "filter_kind": [FILTER_KIND_AMOUNT],
        FILTER_KIND_AMOUNT: (Tender.AMOUNT_RANGE_0, Tender.AMOUNT_RANGE_1),
    },
    {
        "name": "Handeco",
        "contacts_email": ["joseph.ramos@handeco.org"],
        "filter_kind": [],
    },
    {
        "name": "Réseau Gesat",
        "contacts_email": ["denis.charrier@reseau-gesat.com"],
        "filter_kind": [],
    },
    {
        "name": "IRIAE HDF",
        "contacts_email": ["iluu@iriaehdf.com"],
        "filter_kind": [FILTER_KIND_PERIMETERS],
        FILTER_KIND_PERIMETERS: Q(name="Hauts-de-France") | Q(region_code="32"),
    },
    {
        "name": "URSIAE",
        "contacts_email": ["developpement.ursiae974@gmail.com"],
        "filter_kind": [FILTER_KIND_PERIMETERS],
        FILTER_KIND_PERIMETERS: Q(name="La Réunion") | Q(region_code="04"),
    },
    {
        "name": "URSIAE",
        "contacts_email": ["emmanuelle.daviau@ursiea.org"],
        # Grand Est
        "filter_kind": [FILTER_KIND_PERIMETERS],
        FILTER_KIND_PERIMETERS: Q(name="Grand Est") | Q(region_code="44"),
    },
]
