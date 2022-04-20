import logging

import httpx
from django.conf import settings
from huey.contrib.djhuey import task


logger = logging.getLogger(__name__)


BASE_URL = "https://hooks.slack.com/services/"


def get_default_params():
    return {}


def get_default_client(params={}):
    params |= get_default_params()
    headers = {
        "user-agent": "betagouv-lemarche/0.0.1",
    }
    client = httpx.Client(
        params=params, headers=headers, auth=(settings.MAILJET_MASTER_API_KEY, settings.MAILJET_MASTER_API_SECRET)
    )
    return client


@task()
def send_message_to_channel(text: str, service_id: str, client: httpx.Client = None):
    """Huey task to send message to specific payload for specific slack service

    Args:
        payload (dict): payload for serivce
        service_id (str): service id of the service (ex of service: Webhook)
        client (httpx.Client, optional): client to send requests. Defaults to None.

    Raises:
        e: httpx.HTTPStatusError
    """
    if settings.SLACK_NOTIF_IS_ACTIVE:
        if not client:
            client = get_default_client()

        try:
            data = {"text": text}
            response = client.post(f"{BASE_URL}{service_id}", json=data)
            response.raise_for_status()
            logger.info("send message to slack")
            logger.info(response.json())
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
