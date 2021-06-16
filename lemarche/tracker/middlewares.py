from django.conf import settings
from datetime import datetime
import httpx
import logging
import json
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

VERSION = 1
DEFAULT_PAYLOAD = {
    '_v': VERSION,
    'timestamp': None,
    'order': 0,
    'session_id': None,
    'env': settings.BITOUBI_ENV,
    'page': None,
    'action': None,
    'meta': {},
    'client_context': {},
    'server_context': {},
}


def track(page: str, action: str, *, meta: dict = {}, session_id: str = None, client_context: dict = {}):
    # TODO : Make Async / non-blocking
    set_meta = {'source': 'bitoubi_api'}

    if not session_id:
        # Tracker requires a session_id
        token = meta.get('token')
        session_id = f"{token.ljust(8,'0')}-1111-2222-3333-444444444444"

    set_payload = {
            'timestamp': datetime.now().isoformat(),
            'page': page,
            'session_id': session_id,
            'action': action,
            'meta': json.dumps(meta | set_meta),
            'client_context': client_context,
    }

    payload = DEFAULT_PAYLOAD | set_payload
    print(json.dumps(payload, indent=2))

    try:
        r = httpx.post(
            f"{settings.TRACKER_HOST}/track",
            json=payload
        )
        logger.info("Logged to %s", r.url)
        logger.info("Log result: %s", r.text)
        if r.status_code != httpx.codes.OK:
            print(r.text)
            logger.critical("HEY YOU !")
    except httpx.HTTPError:
        logger.warning("Failed to submit tracker")


class TokenVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.GET.get("token", '0')
        page = request.path

        if page not in ['/favicon.ico']:
            track(page, 'load', meta={'token': token})

        response = self.get_response(request)
        return response
