import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException


logger = logging.getLogger(__name__)


def get_api_instance():
    api_instance = sib_api_v3_sdk.SMTPApi(sib_api_v3_sdk.ApiClient(settings.brevo_configuration))
    return api_instance


ENV_NOT_ALLOWED = ("dev", "test")


@task()
def send_html_email(to: list, sender: dict, html_content: str, headers: dict = {}):
    api_instance = get_api_instance()
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to, headers=headers, html_content=html_content, sender=sender
    )  # SendSmtpEmail | Values to send a transactional email
    try:
        # Send a transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


@task()
def send_transactionnel_email(to: list, sender: dict, template_id: int, params_template: dict, headers: dict = {}):
    """Send transactionnel email

    Args:
        to (list): List of dict, ex : [{"email": "testmail@example.com", "name": "John Doe"}]
        template_id (int): template id of email
        params_template (dict): Paramaters of template, ec {"name": "John", "surname": "Doe"}
        headers (dict, optional): Custom headers of emails. Defaults to {}.
    """
    api_instance = get_api_instance()
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to, template_id=template_id, sender=sender, params=params_template, headers=headers
    )  # SendSmtpEmail | Values to send a transactional email
    try:
        # Send a transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
