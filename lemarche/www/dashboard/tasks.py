from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone

from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


# TODO: make async (celery)
def send_siae_user_request_email(siae_user_request):
    """
    Send request to the assignee
    """
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject = (
        email_subject_prefix + f"{siae_user_request.initiator.full_name} souhaite se rattacher à votre structure"
    )
    email_body = render_to_string(
        "dashboard/siae_user_request_email_body.txt",
        {
            "assignee_full_name": siae_user_request.assignee.full_name,
            "user_full_name": siae_user_request.initiator.full_name,
            "siae_name": siae_user_request.siae.name_display,
            "siae_edit_users_url": f"https://{get_domain_url()}{reverse_lazy('dashboard:siae_edit_users', args=[siae_user_request.siae.slug])}",  # noqa
        },
    )
    recipient_list = whitelist_recipient_list([siae_user_request.assignee.email])

    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )

    # log email
    log_item = {
        "action": "email_sent",
        "email_to": recipient_list,
        "email_subject": email_subject,
        "email_body": email_body,
        "email_timestamp": timezone.now().isoformat(),
    }
    siae_user_request.logs.append(log_item)
    siae_user_request.save()


def send_siae_user_request_response_email(siae_user_request, response=None):
    """
    Send request response (True or False) to the initial user
    """
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject_text = "Nouveau collaborateur" if response else "Rattachement refusé"
    email_subject = email_subject_prefix + email_subject_text
    email_template = (
        "dashboard/siae_user_request_response_true_email_body.txt"
        if response
        else "dashboard/siae_user_request_response_false_email_body.txt"
    )
    email_body = render_to_string(
        email_template,
        {
            "assignee_full_name": siae_user_request.assignee.full_name,
            "user_full_name": siae_user_request.initiator.full_name,
            "siae_name": siae_user_request.siae.name_display,
            "siae_edit_users_url": f"https://{get_domain_url()}{reverse_lazy('dashboard:siae_edit_users', args=[siae_user_request.siae.slug])}",  # noqa
        },
    )
    recipient_list = whitelist_recipient_list([siae_user_request.initiator.email])

    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )

    # log email
    log_item = {
        "action": "email_sent",
        "email_to": recipient_list,
        "email_subject": email_subject,
        "email_body": email_body,
        "email_timestamp": timezone.now().isoformat(),
    }
    siae_user_request.logs.append(log_item)
    siae_user_request.save()
