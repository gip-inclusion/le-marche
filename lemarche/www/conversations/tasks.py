from lemarche.conversations.models import Conversation
from lemarche.siaes.models import Siae
from lemarche.utils.emails import send_email_html, whitelist_recipient_list


def send_first_email_from_conversation(conv: Conversation):
    siae: Siae = conv.siae
    send_email_html(
        recipient_list=whitelist_recipient_list([siae.contact_email]),
        email_subject=conv.title,
        email_body=conv.initial_body_message,
        from_email=conv.email_sender_buyer_encoded,
    )


def send_email_from_conversation(
    conv: Conversation, user_kind: str, email_subject: str, email_body: str, html_email: str
):
    if user_kind == Conversation.USER_KIND_SENDER_TO_SIAE:
        send_email_html(
            recipient_list=whitelist_recipient_list([conv.email_sender_siae]),
            email_subject=email_subject,
            email_body=email_body,
            html_email=html_email,
            from_email=conv.email_sender_buyer_encoded,
        )
    elif user_kind == Conversation.USER_KIND_SENDER_TO_BUYER:
        send_email_html(
            recipient_list=whitelist_recipient_list([conv.email_sender_buyer]),
            email_subject=email_subject,
            email_body=email_body,
            html_email=html_email,
            from_email=conv.email_sender_siae_encoded,
        )
    # api_brevo.send_transactionnel_email(
    #     to={"email": siae.contact_email, "name": siae.contact_full_name},
    #     sender={"email": conv.email_sender, "name": "John Doe"},
    #     template_id=1,
    #     params_template={"body_message": conv.data[0].get("body_message")},
    # )
