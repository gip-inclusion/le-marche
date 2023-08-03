import re

from django.conf import settings
from django.core.mail import send_mail
from huey.contrib.djhuey import task


EMAIL_SUBJECT_PREFIX = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""


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
