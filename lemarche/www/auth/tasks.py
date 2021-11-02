from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


# TODO: make async (celery)
def send_welcome_email(user):
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject = email_subject_prefix + f"Bienvenue {user.first_name} !"
    email_body_html = render_to_string("auth/signup_welcome_email_body.html", {})
    email_body_text = strip_tags(email_body_html)

    send_mail(
        subject=email_subject,
        message=email_body_text,
        html_message=email_body_html,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=whitelist_recipient_list([user.email]),
        fail_silently=False,
    )


# TODO: make async (celery)
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

    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.NOTIFY_EMAIL],
        fail_silently=False,
    )
