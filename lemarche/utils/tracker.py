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
import uuid
from datetime import datetime

import httpx
from crawlerdetect import CrawlerDetect
from django.conf import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

crawler_detect = CrawlerDetect()


VERSION = 1

TRACKER_IGNORE_LIST = [
    "static/",
    "admin/",
    "select2/",
    "api/perimeters/autocomplete",
    "track/",  # avoid duplicate tracking
]

USER_KIND_MAPPING = {
    "SIAE": "4",
    "BUYER": "3",
    "PARTNER": "6",
    "ADMIN": "5",
}

DEFAULT_PAYLOAD = {
    "_v": VERSION,
    "timestamp": datetime.now().astimezone().isoformat(),
    "env": settings.BITOUBI_ENV,
    "page": "",
    "action": "load",
    "meta": {"source": "bitoubi_api"},  # needs to be stringifyed...
    "session_id": None,
    "order": 0,
}


def extract_meta_from_request(request):
    return {
        **request.GET,
        "is_admin": request.COOKIES.get("isAdmin", "false") == "true",
        "user_type": USER_KIND_MAPPING.get(request.user.kind) if request.user.id else "",
        "user_id": request.user.id if request.user.id else None,
        "token": request.GET.get("token", ""),
        "cmp": request.GET.get("cmp", ""),
    }


def track(page: str = "", action: str = "load", meta: dict = {}, session_id: str = None, order: int = 0):  # noqa B006

    # Don't log in dev
    if settings.BITOUBI_ENV != "dev":

        # extract_sessionid_from_request
        if session_id:
            # transform the django sessionid to a uuid
            session_id = str(uuid.uuid3(uuid.NAMESPACE_OID, session_id))
        else:
            # TODO: generate and use uuid4-style session_ids, unique to a user's session
            # https://data-flair.training/blogs/django-sessions/
            token = meta.get("token") or "0"
            session_id = f"{token.ljust(8,'0')}-1111-2222-AAAA-444444444444"

        set_payload = {
            "timestamp": datetime.now().isoformat(),
            "page": page,
            "action": action,
            "session_id": session_id,
            "order": order,
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
                session_id = request.COOKIES.get("sessionid", None)
                track(
                    page=page,
                    action="load",
                    meta=meta,
                    session_id=session_id,
                )

        response = self.get_response(request)
        return response
