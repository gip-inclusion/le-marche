from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string


# TODO: make async (celery)
def send_signup_notification_email(user):
    email_body = render_to_string(
        "auth/signup_notification_email.txt",
        {
            "user_email": user.email,
            "user_id": user.id,
            "user_last_name": user.last_name,
            "user_first_name": user.first_name,
            "user_kind_display": user.get_kind_display(),
            "domain": Site.objects.get_current().domain,
        },
    )

    send_mail(
        subject="C4 Notif: Inscription d'un nouvel utilisateur",
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.NOTIFY_EMAIL],
        fail_silently=False,
    )
