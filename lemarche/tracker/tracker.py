import json
import logging
from datetime import datetime

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


VERSION = 1

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

# TODO : add event trackers for
# - directory_csv (csv download event)
# - directory_list (directory page access event)
# - directory_search (directory search event)
# Not used that much :
# - adopt (adoption event)
# - adopt_search (an adoption search event)


def track(page: str, action: str, *, meta: dict = {}, session_id: str = None, client_context: dict = {}):  # noqa B006
    # TODO : Make Async / non-blocking.
    # But unless the whole application becomes async,
    # the only way would be to use threads, which is another problem in itself.
    # However, nothing keeps the Django app from writing
    # to the tracking database directly, which would be magnitudes faster.

    # Don't log in dev
    if settings.BITOUBI_ENV != "dev":

        set_meta = {"source": "bitoubi_api"}

        if not session_id:
            # TODO: generate and use uuid4-style session_ids, unique to a user's session
            # https://data-flair.training/blogs/django-sessions/
            token = meta.get("token") or "0"
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
