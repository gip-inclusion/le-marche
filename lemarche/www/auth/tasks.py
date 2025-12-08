from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from lemarche.conversations.models import TemplateTransactional
from lemarche.users.models import User
from lemarche.utils.apis import api_slack
from lemarche.utils.emails import send_mail_async, whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


def generate_password_reset_link(user):
    domain = get_domain_url()
    base64_encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    reset_url_args = {"uidb64": base64_encoded_id, "token": token}
    reset_path = reverse("auth:password_reset_confirm", kwargs=reset_url_args)
    return f"https://{domain}{reset_path}"


def notify_team_new_user(user):
    email_subject = f"Marché de l'inclusion : inscription d'un nouvel utilisateur ({user.get_kind_display()})"
    email_body = render_to_string(
        "auth/signup_notification_email_body.txt",
        {
            "user_email": user.email,
            "user_id": user.id,
            "user_last_name": user.last_name,
            "user_first_name": user.first_name,
            "user_kind_display": user.get_kind_display(),
            "domain": get_domain_url(),
        },
    )

    send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=[settings.NOTIFY_EMAIL],
    )

    # send slack notification if the channel is set and the user is a siae
    if settings.SLACK_WEBHOOK_C4_NEW_SIAE_USER_NOTIFICATION_CHANNEL and user.kind == User.KIND_SIAE:
        api_slack.send_message_to_channel(
            text=email_body, service_id=settings.SLACK_WEBHOOK_C4_NEW_SIAE_USER_NOTIFICATION_CHANNEL
        )


def send_new_user_password_reset_link(user: User, template_code: str = "NEW_USER_PASSWORD_RESET"):
    email_template = TemplateTransactional.objects.get(code=template_code)
    recipient_list = whitelist_recipient_list([user.email])
    if len(recipient_list):
        recipient_email = recipient_list[0]
        recipient_name = user.full_name

        variables = {
            "USER_ID": user.id,
            "USER_FIRST_NAME": user.first_name,
            "USER_EMAIL": user.email,
            "PASSWORD_RESET_LINK": generate_password_reset_link(user),
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            recipient_content_object=user,
        )
