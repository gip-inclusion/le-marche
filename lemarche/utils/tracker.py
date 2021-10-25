import json
import logging
from datetime import datetime

import httpx
from crawlerdetect import CrawlerDetect
from django.conf import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

crawler_detect = CrawlerDetect()


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

# TODO: add event trackers for
# - directory_list (directory page access event) / duplicate with directory_search
# Not used that much :
# - adopt (adoption event) / already have adopt_search...


def track(
    page: str,
    action: str,
    meta: dict = {},
    session_id: str = None,
    client_context: dict = {},
    server_context: dict = {},
):  # noqa B006
    # TODO: Make Async / non-blocking.
    # But unless the whole application becomes async,
    # the only way would be to use threads, which is another problem in itself.
    # However, nothing keeps the Django app from writing
    # to the tracking database directly, which would be magnitudes faster.

    # Don't log in dev
    if settings.BITOUBI_ENV != "devtest":

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
            "server_context": server_context,
        }

        payload = DEFAULT_PAYLOAD | set_payload

        try:
            r = httpx.post(f"{settings.TRACKER_HOST}/track", json=payload)
            r.raise_for_status()
            logger.info("Tracker sent")
        except httpx.HTTPError as e:
            logger.exception(e)
            logger.warning("Failed to submit tracker")


TRACKER_IGNORE_LIST = [
    "static/",
    "api/perimeters",
]

USER_KIND_MAPPING = {
    "SIAE": "4",
    "BUYER": "3",
    "PARTNER": "6",
    "ADMIN": "5",
}


class TrackerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        page = request.path
        request_ua = request.META.get("HTTP_USER_AGENT", "")

        # Final checks before calling the track() function
        # - make sure no "ignored" keyword is in the path
        # - make sure the request doesn't come from a crawler
        if all([s not in page for s in TRACKER_IGNORE_LIST]):
            is_crawler = crawler_detect.isCrawler(request_ua)
            if not is_crawler:
                # build meta & co
                meta = {
                    "is_admin": request.COOKIES.get("isAdmin", "false"),
                    "user_type": USER_KIND_MAPPING.get(request.user.kind) if request.user.id else None,
                    "user_id": request.user.id if request.user.id else None,
                    "token": request.GET.get("token", "0"),
                    "user_cookie_type": request.COOKIES.get("leMarcheTypeUsagerV2", None),
                    "cmp": request.GET.get("cmp", None),
                }
                session_id = request.COOKIES.get("session_id", None)
                client_context = {"referer": request.META.get("HTTP_REFERER", ""), "user_agent": request_ua}
                server_context = {
                    "client_ip": request.META.get("HTTP_X_FORWARDED_FOR", ""),
                }
                track(
                    page,
                    "load",
                    meta=meta,
                    session_id=session_id,
                    client_context=client_context,
                    server_context=server_context,
                )

        response = self.get_response(request)
        return response
