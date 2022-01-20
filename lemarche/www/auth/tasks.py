from huey.contrib.djhuey import task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url
from lemarche.utils.apis import api_mailjet
from lemarche.users.models import User


def send_welcome_email(user):
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject = email_subject_prefix + f"Bienvenue {user.first_name} !"
    email_body = render_to_string("auth/signup_welcome_email_body.txt", {})

    _send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=whitelist_recipient_list([user.email]),
    )


def send_signup_notification_email(user):
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject = (
        email_subject_prefix
        + f"Marché de l'inclusion : inscription d'un nouvel utilisateur ({user.get_kind_display()})"
    )
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

    _send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=[settings.NOTIFY_EMAIL],
    )


def add_to_contact_list(user):
    """Add user to contactlist

    Args:
        user (User): the user how will be added in the contact list
    """
    properties = {
        "nom": user.first_name,
        "prénom": user.last_name,
        "pays": "france",
        "nomsiae": user.company_name,
        "poste": user.position,
    }
    api_mailjet.add_to_contact_list_async(user.email, properties, user.kind)


@task()
def _send_mail_async(
    email_subject,
    email_body,
    recipient_list,
    from_email=settings.DEFAULT_FROM_EMAIL,
    fail_silently=False,
):
    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
    )
