from django.core.mail import send_mail

from lemarche.conversations.models import Conversation
from lemarche.siaes.models import Siae
from lemarche.utils.emails import whitelist_recipient_list


def send_first_email_from_conversation(conv: Conversation):
    siae: Siae = conv.siae
    send_mail(
        subject=conv.title,
        message=conv.initial_body_message,
        from_email=conv.email_sender_buyer_encoded,
        recipient_list=whitelist_recipient_list([siae.contact_email]),
        fail_silently=False,
    )


def send_email_from_conversation(
    conv: Conversation, user_kind: str, email_subject: str, email_body: str, email_body_html: str
):
    if user_kind == Conversation.USER_KIND_SENDER_TO_SIAE:
        send_mail(
            subject=email_subject,
            message=email_body,
            html_message=email_body_html,
            from_email=conv.email_sender_buyer_encoded,
            recipient_list=whitelist_recipient_list([conv.email_sender_siae]),
            fail_silently=False,
        )
    elif user_kind == Conversation.USER_KIND_SENDER_TO_BUYER:
        send_mail(
            subject=email_subject,
            message=email_body,
            html_message=email_body_html,
            from_email=conv.email_sender_siae_encoded,
            recipient_list=whitelist_recipient_list([conv.email_sender_buyer]),
            fail_silently=False,
        )
    # api_brevo.send_transactionnel_email(
    #     to={"email": siae.contact_email, "name": siae.contact_full_name},
    #     sender={"email": conv.email_sender, "name": "John Doe"},
    #     template_id=1,
    #     params_template={"body_message": conv.data[0].get("body_message")},
    # )
