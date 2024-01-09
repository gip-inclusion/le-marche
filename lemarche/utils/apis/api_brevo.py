import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException


logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")


def get_default_client():
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


@task()
def send_html_email(to: list, sender: dict, html_content: str, headers: dict = {}):
    client = get_default_client()
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, headers=headers, html_content=html_content, sender=sender)
    try:
        # Send a transactional email
        api_response = client.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


@task()
def send_transactional_email_with_template(
    template_id: int,
    subject: str,
    recipient_email: str,
    recipient_name: str,
    variables: dict,
    from_email=settings.DEFAULT_FROM_EMAIL_BREVO,
    from_name=settings.DEFAULT_FROM_NAME_BREVO,
):
    client = get_default_client()
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"email": from_email, "name": from_name},
        to=[{"email": recipient_email, "name": recipient_name}],
        subject=subject,
        template_id=template_id,
        params=variables,
    )

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            response = client.send_transac_email(send_smtp_email)
            logger.info("Brevo: send transactional email with template")
            return response
        except ApiException as e:
            print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
    else:
        logger.info("Brevo: email not sent (DEV or TEST environment detected)")
