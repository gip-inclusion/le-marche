import logging

import sib_api_v3_sdk
from django.conf import settings
from huey.contrib.djhuey import task
from sib_api_v3_sdk.rest import ApiException


logger = logging.getLogger(__name__)

ENV_NOT_ALLOWED = ("dev", "test")


def get_config():
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY
    return config


def get_api_client():
    config = get_config()
    return sib_api_v3_sdk.ApiClient(config)


@task()
def send_transactional_email_with_template(
    template_id: int,
    subject: str,
    recipient_email: str,
    recipient_name: str,
    variables: dict,
    from_email=settings.DEFAULT_FROM_EMAIL,
    from_name=settings.DEFAULT_FROM_NAME,
):
    api_client = get_api_client()
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"email": from_email, "name": from_name},
        to=[{"email": recipient_email, "name": recipient_name}],
        subject=subject,
        template_id=template_id,
        params=variables,
    )

    if settings.BITOUBI_ENV not in ENV_NOT_ALLOWED:
        try:
            response = api_instance.send_transac_email(send_smtp_email)
            logger.info("Brevo: send transactional email with template")
            return response
        except ApiException as e:
            print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
    else:
        logger.info("Brevo: email not sent (DEV or TEST environment detected)")
