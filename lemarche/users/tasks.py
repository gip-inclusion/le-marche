from lemarche.conversations.models import TemplateTransactional


def notify_user_onboarded(user):
    """Send an email when the user is onboarded."""
    email_template = TemplateTransactional.objects.get(code="USER_ONBOARDING_CONFIRMED")
    variables = {"PRENOM": user.first_name}

    email_template.send_transactional_email(
        recipient_email=user.email,
        recipient_name=user.full_name,
        variables=variables,
        recipient_content_object=user,
        parent_content_object=user,
    )
