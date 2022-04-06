from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.utils.apis import api_mailjet
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


EMAIL_SUBJECT_PREFIX = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""

FILTER_KIND_AMOUNT = "amount"
FILTER_KIND_COMPANY = "company"
FILTER_KIND_PERIMETERS = "perimeters"

PARTNER_FILTERS = [
    {
        "name": "Linklusion",
        "filter_kind": [FILTER_KIND_COMPANY],
        "companies_filter": Q(kind=Siae.KIND_EA) | Q(kind=Siae.KIND_TI),
        "contacts_email": ["jalil@linklusion.fr"],
    },
    {
        "name": "Adie",
        "filter_kind": [FILTER_KIND_AMOUNT],
        "amount_limit": 50000,
        "contacts_email": ["csaintaurens@adie.org", "phenric@adie.org"],
    },
    {
        "name": "Handeco",
        "filter_kind": [FILTER_KIND_COMPANY],
        "companies_filter": Q(kind=Siae.KIND_EA) | Q(kind=Siae.KIND_TI),
        "contacts_email": ["joseph.ramos@handeco.org"],
    },
    {
        "name": "Réseau Gesat",
        "filter_kind": [FILTER_KIND_COMPANY],
        "companies_filter": Q(kind=Siae.KIND_EA) | Q(kind=Siae.KIND_TI),
        "contacts_email": ["denis.charrier@reseau-gesat.com"],
    },
    {
        "name": "IRIAE HDF",
        "filter_kind": [FILTER_KIND_COMPANY, FILTER_KIND_PERIMETERS],
        "companies_filter": Q(kind=Siae.KIND_AI) | Q(kind=Siae.KIND_TI),
        "perimeters_filter": Q(name="Hauts-de-France"),
        "contacts_email": ["iluu@iriaehdf.com"],
    },
    {
        "name": "URSIAE",
        "filter_kind": [FILTER_KIND_COMPANY, FILTER_KIND_PERIMETERS],
        "companies_filter": Q(kind=Siae.KIND_AI) | Q(kind=Siae.KIND_TI),
        "perimeters_filter": Q(name="La Réunion"),
        "contacts_email": ["developpement.ursiae974@gmail.com"],
    },
    {
        "name": "URSIAE",
        # Grand Est
        "filter_kind": [FILTER_KIND_COMPANY, FILTER_KIND_PERIMETERS],
        "companies_filter": Q(kind=Siae.KIND_AI) | Q(kind=Siae.KIND_TI),
        "perimeters_filter": Q(name="Grand Est"),
        "contacts_email": ["emmanuelle.daviau@ursiea.org"],
    },
]


# @task()
def send_tender_emails(tender: Tender):
    """
    TODO: filter on source="EMAIL" ?
    """
    for siae in tender.siaes.all():
        send_tender_email_to_siae(tender, siae)
    tender.tendersiae_set.update(email_send_date=timezone.now())
    for partner in PARTNER_FILTERS:
        send_email = False
        if FILTER_KIND_AMOUNT in tender.get("filter_kind"):
            if tender.amount <= tender.get("amount"):
                send_email = True

        if FILTER_KIND_COMPANY in tender.get("filter_kind"):
            if tender.siaes.filter(tender.get("companies_filter")).exists():
                send_email = True
            else:
                send_email = False
        if FILTER_KIND_PERIMETERS in tender.get("filter_kind"):
            if tender.perimeters.filter(tender.get("perimeters_filter")).exists():
                send_email = True
            else:
                send_email = False
        if send_email:
            send_tender_email_to_partner(tender, partner)


def send_tender_email_to_partner(tender: Tender, partner: dict):
    email_subject = (
        EMAIL_SUBJECT_PREFIX + f"{tender.author.company_name} a besoin de vous sur le marché de l'inclusion"
    )
    recipient_list = whitelist_recipient_list(partner.get("contacts_email"))
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        variables = {
            "BUYER_COMPANY": tender.author.company_name,
            "RESPONSE_KIND": tender.get_kind_display(),
            "SECTORS": tender.get_sectors_names,
            "PERIMETERS": tender.get_perimeters_names,
            "TENDER_URL": f"https://{get_domain_url()}{tender.get_absolute_url()}",
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_PRESENTATION_TEMPLATE_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
        )


# @task()
def send_tender_email_to_siae(tender: Tender, siae: Siae):
    email_subject = (
        EMAIL_SUBJECT_PREFIX + f"{tender.author.company_name} a besoin de vous sur le marché de l'inclusion"
    )
    recipient_list = whitelist_recipient_list([siae.contact_email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        variables = {
            "FULL_NAME": siae.contact_first_name,
            "BUYER_COMPANY": tender.author.company_name,
            "RESPONSE_KIND": tender.get_kind_display(),
            "SECTORS": tender.get_sectors_names,
            "PERIMETERS": tender.get_perimeters_names,
            "TENDER_URL": f"https://{get_domain_url()}{tender.get_absolute_url()}",
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_PRESENTATION_TEMPLATE_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
        )
