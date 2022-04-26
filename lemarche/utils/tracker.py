# TODO: add event trackers for
# - directory_list (directory page access event) / duplicate with directory_search
# Not used that much :
# - adopt (adoption event) / already have adopt_search...

# TODO: Make Async / non-blocking.
# But unless the whole application becomes async,
# the only way would be to use threads, which is another problem in itself.
# However, nothing keeps the Django app from writing
# to the tracking database directly, which would be magnitudes faster.

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

TRACKER_IGNORE_LIST = [
    "/static",
    "/favicon.ico",
    "/admin",
    "/select2",
    "/api/perimeters/autocomplete",
    "/track",  # avoid duplicate tracking
]

DEFAULT_PAYLOAD = {
    "_v": VERSION,
    "timestamp": datetime.now().astimezone().isoformat(),
    "env": settings.BITOUBI_ENV,
    "page": "",
    "action": "load",
    "meta": {"source": "bitoubi_api"},  # needs to be stringifyed...
    "session_id": "00000000-1111-2222-aaaa-444444444444",
    "order": 0,
}


def extract_meta_from_request(request):
    return {
        **request.GET,
        "is_admin": request.COOKIES.get("isAdmin", "false") == "true",
        "user_type": request.user.kind if request.user.id else "",
        "user_id": request.user.id if request.user.id else None,
        "token": request.GET.get("token", ""),
        "cmp": request.GET.get("cmp", ""),
    }


def track(page: str = "", action: str = "load", meta: dict = {}):  # noqa B006

    # Don't log in dev
    if settings.BITOUBI_ENV != "dev":
        set_payload = {
            "timestamp": datetime.now().isoformat(),
            "page": page,
            "action": action,
            "meta": json.dumps(DEFAULT_PAYLOAD["meta"] | meta),
        }

        payload = DEFAULT_PAYLOAD | set_payload

        try:
            r = httpx.post(f"{settings.TRACKER_HOST}/track", json=payload)
            r.raise_for_status()
            # logger.info("Tracker sent")
        except httpx.HTTPError as e:
            logger.exception(e)
            logger.warning("Failed to submit tracker")


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
                meta = extract_meta_from_request(request)
                track(
                    page=page,
                    action="load",
                    meta=meta,
                )

        response = self.get_response(request)
        return response
