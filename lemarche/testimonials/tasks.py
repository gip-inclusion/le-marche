import logging

from django.urls import reverse

from lemarche.conversations.models import TemplateTransactional
from lemarche.testimonials import constants as testimonial_constants
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


logger = logging.getLogger(__name__)


def send_testimonial_request_email(testimonial, sender_name: str) -> None:
    """
    Envoie l'email d'invitation au client pour qu'il dépose son témoignage.
    Ne fait rien si le template est inactif ou si l'email est hors whitelist.
    """
    try:
        email_template = TemplateTransactional.objects.get(
            code=testimonial_constants.BREVO_TESTIMONIAL_REQUEST_TEMPLATE_CODE
        )
    except TemplateTransactional.DoesNotExist:
        logger.error("Template Brevo %s introuvable", testimonial_constants.BREVO_TESTIMONIAL_REQUEST_TEMPLATE_CODE)
        return

    recipient_list = whitelist_recipient_list([testimonial.client_email])
    if not recipient_list:
        return

    testimonial_url = (
        f"https://{get_domain_url()}"
        f"{reverse('testimonials:submit', kwargs={'token': testimonial.token})}"
    )

    variables = {
        "SIAE_NAME": testimonial.siae.name,
        "SENDER_NAME": sender_name,
        "CUSTOM_MESSAGE": testimonial.custom_message,
        "TESTIMONIAL_URL": testimonial_url,
    }

    email_template.send_transactional_email(
        recipient_email=recipient_list[0],
        recipient_name=testimonial.client_email,
        variables=variables,
        recipient_content_object=None,
        parent_content_object=testimonial,
    )


def send_testimonial_received_email(testimonial) -> None:
    """
    Notifie les membres de la SIAE qu'un témoignage vient d'être soumis.
    Ne fait rien si le template est inactif ou si aucun membre n'est joignable.
    """
    try:
        email_template = TemplateTransactional.objects.get(
            code=testimonial_constants.BREVO_TESTIMONIAL_RECEIVED_TEMPLATE_CODE
        )
    except TemplateTransactional.DoesNotExist:
        logger.error("Template Brevo %s introuvable", testimonial_constants.BREVO_TESTIMONIAL_RECEIVED_TEMPLATE_CODE)
        return

    dashboard_url = (
        f"https://{get_domain_url()}"
        f"{reverse('dashboard_siaes:siae_testimonial_list', kwargs={'slug': testimonial.siae.slug})}"
    )

    variables = {
        "SIAE_NAME": testimonial.siae.name,
        "TESTIMONIAL_CONTENT": testimonial.content,
        "AUTHOR_FIRST_NAME": testimonial.author_first_name,
        "AUTHOR_ORGANIZATION": testimonial.author_organization,
        "DASHBOARD_URL": dashboard_url,
    }

    siae_member_emails = list(testimonial.siae.users.values_list("email", flat=True))
    recipient_list = whitelist_recipient_list(siae_member_emails)

    for recipient_email in recipient_list:
        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=testimonial.siae.name,
            variables=variables,
            recipient_content_object=None,
            parent_content_object=testimonial,
        )
