from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender, TenderSiae
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
def send_tender_emails_to_siaes(tender: Tender):
    """
    All corresponding Siae will be contacted
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
        recipient_name = siae.contact_full_name

        variables = {
            "SIAE_CONTACT_FIRST_NAME": siae.contact_first_name,
            "TENDER_AUTHOR_COMPANY": tender.author.company_name,
            "TENDER_KIND": tender.get_kind_display(),
            "TENDER_SECTORS": tender.get_sectors_names,
            "TENDER_PERIMETERS": tender.get_perimeters_names,
            "TENDER_URL": f"https://{get_domain_url()}{tender.get_absolute_url()}",
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_PRESENTATION_TEMPLATE_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
        )


def send_siae_interested_email_to_author(tender: Tender):
    """
    The author is notified (by intervals) when new Siaes show interest (contact_click_date set)
    Intervals:
    - first Siae
    - every 5 Siae
    """
    tender_siae_contact_click_count = TenderSiae.objects.filter(
        tender=tender, contact_click_date__isnull=False
    ).count()

    if tender_siae_contact_click_count > 0:
        if (tender_siae_contact_click_count == 1) or (tender_siae_contact_click_count % 5 == 0):
            if tender_siae_contact_click_count == 1:
                email_subject = EMAIL_SUBJECT_PREFIX + "Une première structure intéressée !"
                template_id = settings.MAILJET_TENDERS_SIAE_INTERESTED_1_TEMPLATE_ID
            else:
                email_subject = EMAIL_SUBJECT_PREFIX + "5 nouvelles structures intéressées !"
                template_id = settings.MAILJET_TENDERS_SIAE_INTERESTED_5_TEMPLATE_ID
            recipient_list = whitelist_recipient_list([tender.author.email])  # tender.contact_email ?
            if recipient_list:
                recipient_email = recipient_list[0] if recipient_list else ""
                recipient_name = tender.author.full_name

                variables = {
                    "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
                    "TENDER_TITLE": tender.title,
                    "TENDER_SIAE_INTERESTED_LIST_URL": f"https://{get_domain_url()}{tender.get_absolute_url()}/structures-interessees",  # noqa
                }

                api_mailjet.send_transactional_email_with_template(
                    template_id=template_id,
                    subject=email_subject,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    variables=variables,
                )
