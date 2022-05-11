from django.conf import settings
from django.template.loader import render_to_string

from lemarche.users.models import User
from lemarche.utils.apis import api_mailjet
from lemarche.utils.emails import send_mail_async
from lemarche.utils.urls import get_domain_url


def send_signup_notification_email(user):
    email_subject = f"Marché de l'inclusion : inscription d'un nouvel utilisateur ({user.get_kind_display()})"
    email_body = render_to_string(
        "auth/signup_notification_email_body.txt",
        {
            "user_email": user.email,
            "user_id": user.id,
            "user_last_name": user.last_name,
            "user_first_name": user.first_name,
            "user_kind_display": user.get_kind_display(),
            "domain": get_domain_url(),
        },
    )

    send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=[settings.NOTIFY_EMAIL],
    )


def get_mailjet_cl_on_signup(user: User):
    if user.kind == user.KIND_SIAE:
        return settings.MAILJET_NL_CL_SIAE_ID
    elif user.kind == user.KIND_BUYER:
        return settings.MAILJET_NL_CL_BUYER_ID
    elif user.kind == user.KIND_PARTNER:
        if user.partner_kind == user.PARTNER_KIND_FACILITATOR:
            return settings.MAILJET_NL_CL_PARTNER_FACILITATORS_ID
        elif user.partner_kind in (user.PARTNER_KIND_NETWORD_IAE, user.PARTNER_KIND_NETWORK_HANDICAP):
            return settings.MAILJET_NL_CL_PARTNER_NETWORKS_IAE_HANDICAP_ID
        elif user.partner_kind == user.PARTNER_KIND_DREETS:
            return settings.MAILJET_NL_CL_PARTNER_DREETS_ID


def add_to_contact_list(user: User, type: str):
    """Add user to contactlist

    Args:
        user (User): the user how will be added in the contact list
        type (String): "signup", OR "buyer_download" or "buyer_search" else raise ValueError
    """
    if type == "signup":
        contact_list_id = get_mailjet_cl_on_signup(user)
    elif type == "buyer_search":
        contact_list_id = settings.MAILJET_NL_CL_BUYER_SEARCH_SIAE_LIST_ID
    elif type == "buyer_download":
        contact_list_id = settings.MAILJET_NL_CL_BUYER_DOWNLOAD_SIAE_LIST_ID
    else:
        raise ValueError("kind must be siae or buyer_download")
    if contact_list_id:
        properties = {
            "nom": user.last_name.capitalize(),
            "prénom": user.first_name.capitalize(),
            "pays": "france",
            "nomsiae": user.company_name.capitalize() if user.company_name else "",
            "poste": user.position.capitalize() if user.position else "",
        }

        api_mailjet.add_to_contact_list_async(user.email, properties, contact_list_id)
