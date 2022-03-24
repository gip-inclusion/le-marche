from django.conf import settings

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.utils.apis import api_mailjet
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


EMAIL_SUBJECT_PREFIX = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""


# @task()
def send_tender_emails_to_siae_list(tender: Tender, siae_found_list):
    for siae in siae_found_list:
        send_tender_email_to_siae(tender, siae)


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
