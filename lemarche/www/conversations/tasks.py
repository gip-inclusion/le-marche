from lemarche.conversations.models import Conversation
from lemarche.siaes.models import Siae


# from lemarche.utils.apis import api_brevo


def send_first_email_from_conversation(conv: Conversation):
    siae: Siae = conv.siae
    args = {
        "to": {"email": siae.contact_email, "name": siae.contact_full_name},
        "sender": {"email": conv.email_sender, "name": "John Doe"},
        "template_id": 1,
        "params_template": {"body_message": conv.data[0].get("body_message")},
    }
    print(args)
    # api_brevo.send_transactionnel_email(
    #     to={"email": siae.contact_email, "name": siae.contact_full_name},
    #     sender={"email": conv.email_sender, "name": "John Doe"},
    #     template_id=1,
    #     params_template={"body_message": conv.data[0].get("body_message")},
    # )
