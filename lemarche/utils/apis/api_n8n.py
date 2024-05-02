import logging

import requests
from django.conf import settings
from huey.contrib.djhuey import task


logger = logging.getLogger(__name__)


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
def send_data_to_webhook(
    data: dict, webhook_url: str = settings.N8N_C4_TENDER_WEBHOOK, client: requests.Session = None
):
    """Huey task to send message to specific payload for specific slack service

    Args:
        data (dict): data for webhook
        webhook_url (str): webhook url of the service
        client (requests.Session, optional): client to send requests. Defaults to None.

    Raises:
        e: requests.HTTPStatusError
    """
    if not client:
        client = get_default_client()

    try:
        response = client.post(webhook_url, data=data)
        response.raise_for_status()
        logger.info("N8N: send data to webhook")
        # logger.info(response.json())  // you'll receive a "HTTP 200" response with a plain text ok indicating that your message posted successfully  # noqa
        return True
    except requests.exceptions.HTTPError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)
        raise e
