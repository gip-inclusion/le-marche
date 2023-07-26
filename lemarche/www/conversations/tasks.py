from lemarche.conversations.models import Conversation
from lemarche.siaes.models import Siae
from lemarche.utils.emails import send_mail_async


def send_first_email_from_conversation(conv: Conversation):
    siae: Siae = conv.siae
    send_mail_async(
        recipient_list=[siae.contact_email],
        email_subject=conv.title,
        email_body=conv.data[0].get("body_message"),
        from_email=conv.email_sender_encoded,
    )
    # api_brevo.send_transactionnel_email(
    #     to={"email": siae.contact_email, "name": siae.contact_full_name},
    #     sender={"email": conv.email_sender, "name": "John Doe"},
    #     template_id=1,
    #     params_template={"body_message": conv.data[0].get("body_message")},
    # )
