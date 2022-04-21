from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

from lemarche.utils.emails import EMAIL_SUBJECT_PREFIX, whitelist_recipient_list


# TODO: make async (celery)
def send_contact_form_email(contact_form_dict):
    email_subject = EMAIL_SUBJECT_PREFIX + "Marché de l'inclusion : demande d'information"
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


# TODO: make async (celery)
def send_contact_form_receipt(contact_form_dict):
    email_subject = EMAIL_SUBJECT_PREFIX + "Suite à votre demande sur le Marché de l'inclusion"
    email_body = render_to_string("pages/contact_form_receipt_email_body.txt", {"form_dict": contact_form_dict})

    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=whitelist_recipient_list([contact_form_dict["email"]]),
        fail_silently=False,
    )
