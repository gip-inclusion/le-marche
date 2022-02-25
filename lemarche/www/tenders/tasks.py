from django.conf import settings
from huey.contrib.djhuey import task

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.utils.apis import api_mailjet
from lemarche.utils.emails import whitelist_recipient_list


EMAIL_SUBJECT_PREFIX = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""


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
        .filter_with_email()
    )

    for siae in siaes_potentially_interested:
        send_emails_tender_to_siae(tender, siae)


@task()
def send_emails_tender_to_siae(tender: Tender, siae: Siae):
    email_subject = EMAIL_SUBJECT_PREFIX + f"{siae.name_display} a besoin de vous sur le marché de l’inclusion"
    recipient_list = whitelist_recipient_list([siae.contact_email])
    recipient_email = recipient_list[0] if recipient_list else ""
    recipient_name = tender.author.full_name

    variables = {
        "FULL_NAME": siae.contact_first_name,
        "RESPONSE_KIND": tender.get_kind_name,
        "SECTORS": tender.get_sectors_names,
        "PERIMETERS": tender.get_perimeters_names,
        "TENDER_URL": tender.get_url,
    }

    api_mailjet.send_transactional_email_with_template(
        template_id=settings.MAILJET_TENDERS_PRESENTATION_TEMPLATE_ID,
        subject=email_subject,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        variables=variables,
    )
