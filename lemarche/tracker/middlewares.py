import json
import logging
from datetime import datetime

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

VERSION = 1
IGNORE_FILTER = [
    "favicon",
    "static",
    "api/perimeters",
]
DEFAULT_PAYLOAD = {
    "_v": VERSION,
    "timestamp": None,
    "order": 0,
    "session_id": None,
    "env": settings.BITOUBI_ENV,
    "page": None,
    "action": None,
    "meta": {},
    "client_context": {},
    "server_context": {},
}


def track(page: str, action: str, *, meta: dict = {}, session_id: str = None, client_context: dict = {}):  # noqa B006
    # TODO : Make Async / non-blocking
    set_meta = {"source": "bitoubi_api"}

    if not session_id:
        # Tracker requires a session_id
        token = meta.get("token")
        session_id = f"{token.ljust(8,'0')}-1111-2222-AAAA-444444444444"

    set_payload = {
        "timestamp": datetime.now().isoformat(),
        "page": page,
        "session_id": session_id,
        "action": action,
        "meta": json.dumps(meta | set_meta),
        "client_context": client_context,
    }

    payload = DEFAULT_PAYLOAD | set_payload

    try:
        r = httpx.post(f"{settings.TRACKER_HOST}/track", json=payload)
        r.raise_for_status()
        logger.info("Tracker sent")
    except httpx.HTTPError as e:
        logger.exception(e)
        logger.warning("Failed to submit tracker")


class TokenVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.GET.get("token", "0")
        page = request.path

        # We make sure no "filtered" keyword is in the path before tracking
        if all([s not in page for s in IGNORE_FILTER]):
            track(page, "load", meta={"token": token})

        response = self.get_response(request)
        return response
