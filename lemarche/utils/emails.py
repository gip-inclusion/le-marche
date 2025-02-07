import re

from django.conf import settings
from django.core.mail import send_mail
from huey.contrib.djhuey import task

from lemarche.utils.apis import api_brevo
from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX


GENERIC_EMAIL_DOMAIN_SUFFIX_LIST = [
    "gmail.com",
    "orange.fr",
    "wanadoo.fr",
    "hotmail.fr",
    "hotmail.com",
    "live.fr",
    "yahoo.fr",
    "yahoo.com",
    "outlook.fr",
    "outlook.com",
    "laposte.net",
    "free.fr",
    "sfr.fr",
    "icloud.com",
    "yandex.com",
    "msn.com",
    "cegetel.net",
    "bbox.fr",
    "yopmail.com",
    "neuf.fr",
    "numericable.fr",
    "gmx.fr",
    "googlemail.com",
]


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


def add_to_contact_list(user, type: str, tender=None):
    """Add user to contactlist

    Args:
        user (User): the user how will be added in the contact list
        type (String): "signup", OR "buyer_search" else raise ValueError
    """
    if type == "signup":
        if user.kind == user.KIND_BUYER:
            api_brevo.create_contact(user=user, list_id=settings.BREVO_CL_SIGNUP_BUYER_ID, tender=tender)
        elif user.kind == user.KIND_SIAE:
            api_brevo.create_contact(user=user, list_id=settings.BREVO_CL_SIGNUP_SIAE_ID)
    elif type == "buyer_search":
        api_brevo.create_contact(user=user, list_id=settings.BREVO_CL_BUYER_SEARCH_SIAE_LIST_ID)
    else:
        raise ValueError("type must be defined")


def update_contact_email_blacklisted(email, email_blacklisted: bool):
    api_brevo.update_contact_email_blacklisted(email, email_blacklisted)


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
