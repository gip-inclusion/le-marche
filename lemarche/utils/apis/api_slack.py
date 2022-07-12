import logging

import requests
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
    client = requests.Session()
    client.params = params
    client.headers = headers
    return client


@task()
def send_message_to_channel(text: str, service_id: str, client: requests.Session = None):
    """Huey task to send message to specific payload for specific slack service

    Args:
        payload (dict): payload for serivce
        service_id (str): service id of the service (ex of service: Webhook)
        client (requests.Session, optional): client to send requests. Defaults to None.

    Raises:
        e: requests.HTTPStatusError
    """
    if settings.SLACK_NOTIF_IS_ACTIVE:
        if not client:
            client = get_default_client()

        try:
            data = {"text": text}
            response = client.post(f"{BASE_URL}{service_id}", json=data)
            response.raise_for_status()
            logger.info("send message to slack")
            # logger.info(response.json())  // you'll receive a "HTTP 200" response with a plain text ok indicating that your message posted successfully  # noqa
            return True
        except requests.exceptions.HTTPError as e:
            logger.error("Error while fetching `%s`: %s", e.request.url, e)
            raise e
