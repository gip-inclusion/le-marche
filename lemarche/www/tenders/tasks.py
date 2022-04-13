from django.conf import settings
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.utils.apis import api_mailjet
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


EMAIL_SUBJECT_PREFIX = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""


# @task()
def send_tender_emails_to_siaes(tender: Tender):
    """
    All corresponding Siae will be contacted
    """
    for siae in tender.siaes.all():
        send_tender_email_to_siae(tender, siae)
    tender.tendersiae_set.update(email_send_date=timezone.now())


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
    print(tender_siae_contact_click_count)
