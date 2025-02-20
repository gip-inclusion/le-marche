from django.urls import reverse_lazy

from lemarche.conversations.models import TemplateTransactional
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url


def send_siae_user_request_email_to_assignee(siae_user_request):
    """
    Send request to the assignee
    """
    email_template = TemplateTransactional.objects.get(code="SIAEUSERREQUEST_ASSIGNEE")
    recipient_list = whitelist_recipient_list([siae_user_request.assignee.email])
    if len(recipient_list):
        recipient_email = recipient_list[0]
        recipient_name = siae_user_request.assignee.full_name

        variables = {
            "SIAE_USER_REQUEST_ID": siae_user_request.id,
            "ASSIGNEE_ID": siae_user_request.assignee.id,
            "ASSIGNEE_FULL_NAME": siae_user_request.assignee.full_name,
            "INITIATIOR_ID": siae_user_request.initiator.id,
            "INITIATOR_FULL_NAME": siae_user_request.initiator.full_name,
            "SIAE_ID": siae_user_request.siae.id,
            "SIAE_NAME": siae_user_request.siae.name_display,
            "SIAE_USERS_URL": f"https://{get_domain_url()}{reverse_lazy('dashboard_siaes:siae_users', args=[siae_user_request.siae.slug])}",  # noqa
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            recipient_content_object=siae_user_request.assignee,
            parent_content_object=siae_user_request,
        )


def send_siae_user_request_response_email_to_initiator(siae_user_request):
    """
    Send request response (True or False) to the initial user
    """
    if siae_user_request.response is not None:
        email_template = (
            TemplateTransactional.objects.get(code="SIAEUSERREQUEST_INITIATOR_RESPONSE_POSITIVE")
            if siae_user_request.response
            else TemplateTransactional.objects.get(code="SIAEUSERREQUEST_INITIATOR_RESPONSE_NEGATIVE")
        )
        recipient_list = whitelist_recipient_list([siae_user_request.initiator.email])
        if len(recipient_list):
            recipient_email = recipient_list[0]
            recipient_name = siae_user_request.initiator.full_name

            variables = {
                "SIAE_USER_REQUEST_ID": siae_user_request.id,
                "ASSIGNEE_ID": siae_user_request.assignee.id,
                "ASSIGNEE_FULL_NAME": siae_user_request.assignee.full_name,
                "INITIATIOR_ID": siae_user_request.initiator.id,
                "INITIATOR_FULL_NAME": siae_user_request.initiator.full_name,
                "SIAE_ID": siae_user_request.siae.id,
                "SIAE_NAME": siae_user_request.siae.name_display,
                "DASHBOARD_URL": f"https://{get_domain_url()}{reverse_lazy('dashboard:home')}",
            }

            email_template.send_transactional_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                variables=variables,
                recipient_content_object=siae_user_request.initiator,
                parent_content_object=siae_user_request,
            )


def send_siae_user_request_reminder_3_days_emails(siae_user_request):
    """
    Send request reminder (after 3 days) to:
    - the initial user
    - to the assignee
    """
    send_siae_user_request_reminder_3_days_email_to_assignee(siae_user_request)
    send_siae_user_request_reminder_3_days_email_to_initiator(siae_user_request)


def send_siae_user_request_reminder_3_days_email_to_assignee(siae_user_request):
    email_template = TemplateTransactional.objects.get(code="SIAEUSERREQUEST_REMINDER_1_ASSIGNEE")
    recipient_list = whitelist_recipient_list([siae_user_request.assignee.email])
    if len(recipient_list):
        recipient_email = recipient_list[0]
        recipient_name = siae_user_request.assignee.full_name

        variables = {
            "SIAE_USER_REQUEST_ID": siae_user_request.id,
            "ASSIGNEE_ID": siae_user_request.assignee.id,
            "ASSIGNEE_FULL_NAME": siae_user_request.assignee.full_name,
            "INITIATIOR_ID": siae_user_request.initiator.id,
            "INITIATOR_FULL_NAME": siae_user_request.initiator.full_name,
            "SIAE_ID": siae_user_request.siae.id,
            "SIAE_NAME": siae_user_request.siae.name_display,
            "SIAE_USERS_URL": f"https://{get_domain_url()}{reverse_lazy('dashboard_siaes:siae_users', args=[siae_user_request.siae.slug])}",  # noqa
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            recipient_content_object=siae_user_request.assignee,
            parent_content_object=siae_user_request,
        )


def send_siae_user_request_reminder_3_days_email_to_initiator(siae_user_request):
    email_template = TemplateTransactional.objects.get(code="SIAEUSERREQUEST_REMINDER_1_INITIATOR")
    recipient_list = whitelist_recipient_list([siae_user_request.initiator.email])
    if len(recipient_list):
        recipient_email = recipient_list[0]
        recipient_name = siae_user_request.initiator.full_name

        variables = {
            "SIAE_USER_REQUEST_ID": siae_user_request.id,
            "ASSIGNEE_ID": siae_user_request.assignee.id,
            "ASSIGNEE_FULL_NAME": siae_user_request.assignee.full_name,
            "INITIATIOR_ID": siae_user_request.initiator.id,
            "INITIATOR_FULL_NAME": siae_user_request.initiator.full_name,
            "SIAE_ID": siae_user_request.siae.id,
            "SIAE_NAME": siae_user_request.siae.name_display,
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            recipient_content_object=siae_user_request.initiator,
            parent_content_object=siae_user_request,
        )


def send_siae_user_request_reminder_8_days_emails(siae_user_request):
    """
    Send request reminder (after 8 days) to:
    - the initial user
    - to the assignee
    """
    send_siae_user_request_reminder_8_days_email_to_assignee(siae_user_request)
    send_siae_user_request_reminder_8_days_email_to_initiator(siae_user_request)


def send_siae_user_request_reminder_8_days_email_to_assignee(siae_user_request):
    email_template = TemplateTransactional.objects.get(code="SIAEUSERREQUEST_REMINDER_2_ASSIGNEE")
    recipient_list = whitelist_recipient_list([siae_user_request.assignee.email])
    if len(recipient_list):
        recipient_email = recipient_list[0]
        recipient_name = siae_user_request.assignee.full_name

        variables = {
            "SIAE_USER_REQUEST_ID": siae_user_request.id,
            "ASSIGNEE_ID": siae_user_request.assignee.id,
            "ASSIGNEE_FULL_NAME": siae_user_request.assignee.full_name,
            "INITIATIOR_ID": siae_user_request.initiator.id,
            "INITIATOR_FULL_NAME": siae_user_request.initiator.full_name,
            "SIAE_ID": siae_user_request.siae.id,
            "SIAE_NAME": siae_user_request.siae.name_display,
            "SIAE_USERS_URL": f"https://{get_domain_url()}{reverse_lazy('dashboard_siaes:siae_users', args=[siae_user_request.siae.slug])}",  # noqa
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            recipient_content_object=siae_user_request.assignee,
            parent_content_object=siae_user_request,
        )


def send_siae_user_request_reminder_8_days_email_to_initiator(siae_user_request):
    email_template = TemplateTransactional.objects.get(code="SIAEUSERREQUEST_REMINDER_2_INITIATOR")
    recipient_list = whitelist_recipient_list([siae_user_request.initiator.email])
    if len(recipient_list):
        recipient_email = recipient_list[0]
        recipient_name = siae_user_request.initiator.full_name

        variables = {
            "SIAE_USER_REQUEST_ID": siae_user_request.id,
            "ASSIGNEE_ID": siae_user_request.assignee.id,
            "ASSIGNEE_FULL_NAME": siae_user_request.assignee.full_name,
            "INITIATIOR_ID": siae_user_request.initiator.id,
            "INITIATOR_FULL_NAME": siae_user_request.initiator.full_name,
            "SIAE_ID": siae_user_request.siae.id,
            "SIAE_NAME": siae_user_request.siae.name_display,
            "SUPPORT_URL": f"https://{get_domain_url()}{reverse_lazy('pages:contact')}?siret={siae_user_request.siae.siret}",  # noqa
        }

        email_template.send_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            recipient_content_object=siae_user_request.initiator,
            parent_content_object=siae_user_request,
        )
