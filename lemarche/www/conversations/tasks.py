from lemarche.conversations.models import Conversation
from lemarche.siaes.models import Siae
from lemarche.utils.emails import send_mail_async, whitelist_recipient_list


def send_first_email_from_conversation(conv: Conversation):
    siae: Siae = conv.siae
    send_mail_async(
        email_subject=conv.title,
        email_body=conv.initial_body_message,
        recipient_list=whitelist_recipient_list([siae.contact_email]),
        from_email=conv.sender_email_buyer_encoded,
    )


def send_email_from_conversation(
    conv: Conversation, user_kind: str, email_subject: str, email_body: str, email_body_html: str
):
    if user_kind == Conversation.USER_KIND_SENDER_TO_SIAE:
        send_mail_async(
            email_subject=email_subject,
            email_body=email_body,
            recipient_list=whitelist_recipient_list([conv.sender_email_siae]),
            from_email=conv.sender_email_buyer_encoded,
            email_body_html=email_body_html,
        )
    elif user_kind == Conversation.USER_KIND_SENDER_TO_BUYER:
        send_mail_async(
            email_subject=email_subject,
            email_body=email_body,
            recipient_list=whitelist_recipient_list([conv.sender_email_buyer]),
            from_email=conv.sender_email_siae_encoded,
            email_body_html=email_body_html,
        )
    # api_brevo.send_transactionnel_email(
    #     to={"email": siae.contact_email, "name": siae.contact_full_name},
    #     sender={"email": conv.sender_email, "name": "John Doe"},
    #     template_id=1,
    #     params_template={"body_message": conv.data[0].get("body_message")},
    # )
