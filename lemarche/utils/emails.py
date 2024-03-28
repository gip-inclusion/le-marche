import re

from django.conf import settings
from django.core.mail import send_mail
from huey.contrib.djhuey import task

from lemarche.users import constants as user_constants
from lemarche.utils.apis import api_brevo, api_hubspot, api_mailjet
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX


def anonymize_email(email):
    email_split = email.split("@")
    email_username = email_split[0]
    email_username_anonymized = email_username[0] + re.sub("[a-z]", "*", email_username[1:-1]) + email_username[-1]
    return "@".join([email_username_anonymized, email_split[1]])


# TODO: wrap this method on every send_mail. ex: use email base layout like C1
def whitelist_recipient_list(recipient_list):
    """
    In non-prod environments, this method will filter out non-'beta.gouv.fr' emails from the recipient_list
    """
    if settings.BITOUBI_ENV == "prod":
        return recipient_list
    return [email for email in recipient_list if (email and email.endswith("beta.gouv.fr"))]


def add_to_contact_list(user, type: str, source: str = user_constants.SOURCE_SIGNUP_FORM):
    """Add user to contactlist

    Args:
        user (User): the user how will be added in the contact list
        type (String): "signup", OR "buyer_download" or "buyer_search" else raise ValueError
    """
    contact_list_id = None
    if type == "signup":
        contact_list_id = api_mailjet.get_mailjet_cl_on_signup(user, source)
        if user.kind == user.KIND_BUYER:
            # TODO: we still use it ?
            api_hubspot.add_user_to_crm(user)
            api_brevo.create_contact(user=user, list_id=settings.BREVO_CL_SIGNUP_BUYER_ID)
    elif type == "buyer_search":
        # contact_list_id = settings.MAILJET_NL_CL_BUYER_SEARCH_SIAE_LIST_ID
        api_brevo.create_contact(user=user, list_id=settings.BREVO_CL_BUYER_SEARCH_SIAE_LIST_ID)
    elif type == "buyer_search_traiteur":
        contact_list_id = settings.MAILJET_NL_CL_BUYER_SEARCH_SIAE_TRAITEUR_LIST_ID
    elif type == "buyer_search_nettoyage":
        contact_list_id = settings.MAILJET_NL_CL_BUYER_SEARCH_SIAE_NETTOYAGE_LIST_ID
    elif type == "buyer_download":
        contact_list_id = settings.MAILJET_NL_CL_BUYER_DOWNLOAD_SIAE_LIST_ID
    else:
        raise ValueError("type must be defined")
    if contact_list_id:
        properties = {
            "nom": user.last_name.capitalize(),
            "prénom": user.first_name.capitalize(),
            "pays": "france",
            "nomsiae": user.company_name.capitalize() if user.company_name else "",
            "poste": user.position.capitalize() if user.position else "",
        }

        api_mailjet.add_to_contact_list_async(user.email, properties, contact_list_id)


@task()
def send_mail_async(
    email_subject,
    email_body,
    recipient_list,
    from_email=settings.DEFAULT_FROM_EMAIL,
    email_body_html=None,
    fail_silently=False,
):
    send_mail(
        subject=f"{EMAIL_SUBJECT_PREFIX}{email_subject}",
        message=email_body,
        html_message=email_body_html,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
    )
