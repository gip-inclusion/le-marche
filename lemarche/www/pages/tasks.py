from django.conf import settings
from django.core.mail import EmailMessage  # send_mail
from django.template.loader import render_to_string


# TODO: make async (celery)
def send_contact_form_email(contact_form_dict):
    email_subject_prefix = f"[{settings.BITOUBI_ENV.upper()}] " if settings.BITOUBI_ENV != "prod" else ""
    email_subject = email_subject_prefix + "Marché de l'inclusion : demande d'information"
    email_body = render_to_string("pages/contact_form_email_body.txt", {"form_dict": contact_form_dict})

    # send_mail(
    #     subject=email_subject,
    #     message=email_body,
    #     from_email=settings.NOTIFY_EMAIL,
    #     recipient_list=[settings.CONTACT_EMAIL],
    #     reply_to=[contact_form_dict["email"]],
    #     fail_silently=False,
    # )

    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=settings.NOTIFY_EMAIL,
        to=[settings.CONTACT_EMAIL],
        reply_to=[contact_form_dict["email"]],
    )
    email.send(fail_silently=False)
