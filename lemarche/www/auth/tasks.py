from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from lemarche.users.models import User
from lemarche.utils.apis import api_hubspot, api_mailjet
from lemarche.utils.emails import EMAIL_SUBJECT_PREFIX, send_mail_async, whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


def generate_password_reset_link(user):
    domain = get_domain_url()
    base64_encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    reset_url_args = {"uidb64": base64_encoded_id, "token": token}
    reset_path = reverse("auth:password_reset_confirm", kwargs=reset_url_args)
    return f"https://{domain}{reset_path}"


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


def send_new_user_password_reset_link(user: User):
    email_subject = EMAIL_SUBJECT_PREFIX + "Finalisez votre inscription sur le marché de l'inclusion"
    recipient_list = whitelist_recipient_list([user.email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = user.full_name

        variables = {
            "USER_FIRST_NAME": user.first_name,
            "PASSWORD_RESET_LINK": generate_password_reset_link(user),
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_NEW_USER_PASSWORD_RESET_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
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
        if user.kind == user.KIND_BUYER:
            api_hubspot.add_user_to_crm(user)
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
