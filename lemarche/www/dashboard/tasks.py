from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


# TODO: make async (celery)
def send_siae_user_request_email(siae_user_request):
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject = (
        email_subject_prefix + f"{siae_user_request.user.full_name} souhaite se rattacher à votre structure"
    )
    email_body = render_to_string(
        "dashboard/siae_user_request_email_body.txt",
        {
            "user_name": siae_user_request.user.full_name,
            "siae_name": siae_user_request.siae.name_display,
            "dashboard_home_url": f"https://{get_domain_url()}{reverse_lazy('dashboard:home')}",
        },
    )

    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=whitelist_recipient_list([siae_user_request.assignee.email]),
        fail_silently=False,
    )
