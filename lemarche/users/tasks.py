from lemarche.conversations.models import TemplateTransactional
from lemarche.users import constants as user_constants


def notify_user_onboarded(user):
    """Send an email when the user is onboarded."""
    code_template_email = (
        "USER_ONBOARDING_CONFIRMED"
        if user.source != user_constants.SOURCE_TALLY_FORM
        else "TALLY_USER_ONBOARDING_CONFIRMED"
    )
    email_template = TemplateTransactional.objects.get(code=code_template_email)
    variables = {"PRENOM": user.first_name}

    email_template.send_transactional_email(
        recipient_email=user.email,
        recipient_name=user.full_name,
        variables=variables,
        recipient_content_object=user,
        parent_content_object=user,
    )
