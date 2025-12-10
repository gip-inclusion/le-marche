from django.urls import reverse_lazy

from lemarche.conversations.models import TemplateTransactional
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


def send_user_invite_colleagues_email(email):
    """
    Send an email to a user inviting them to invite their colleagues.
    """
    email_template = TemplateTransactional.objects.get(code="USER_INVITE_COLLEAGUES")
    recipient_list = whitelist_recipient_list([email])
    if len(recipient_list):
        recipient_email = recipient_list[0]

        variables = {
            "REGISTER_URL": f"https://{get_domain_url()}{reverse_lazy('auth:register')}",
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=None,
            variables=variables,
            recipient_content_object=None,
            parent_content_object=None,
        )

    return True
