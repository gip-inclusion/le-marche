import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from huey.contrib.djhuey import task

from lemarche.utils.constants import EMAIL_SUBJECT_PREFIX


logger = logging.getLogger(__name__)

SLACK_BASE_URL = "https://hooks.slack.com/services/"


@task()
def send_mail_async(
    email_subject,
    email_body,
    recipient_list,
    from_email=settings.DEFAULT_FROM_EMAIL,
    email_body_html=None,
    fail_silently=False,
):
    send_mail(
        subject=f"{EMAIL_SUBJECT_PREFIX}{email_subject}",
        message=email_body,
        html_message=email_body_html,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
    )


@task()
def send_slack_message(text: str, service_id: str = settings.SLACK_WEBHOOK_C4_TECH_NOTIFICATIONS_CHANNEL):
    """Huey task to send message to specific payload for specific slack service

    Args:
        payload (dict): payload for serivce
        service_id (str): service id of the service (ex of service: Webhook)
        client (requests.Session, optional): client to send requests. Defaults to None.

    Raises:
        e: requests.HTTPStatusError
    """
    if settings.SLACK_NOTIF_IS_ACTIVE:
        client = requests.Session(
            headers={
                "user-agent": "betagouv-lemarche/0.0.1",
            }
        )

        try:
            data = {"text": text}
            response = client.post(f"{SLACK_BASE_URL}{service_id}", json=data)
            response.raise_for_status()
            logger.info("Slack: send message to channel")
            return True
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
