# TODO: add event trackers for
# - directory_list (directory page access event) / duplicate with directory_search
# Not used that much :
# - adopt (adoption event) / already have adopt_search...

# TODO: Make Async / non-blocking.
# But unless the whole application becomes async,
# the only way would be to use threads, which is another problem in itself.
# However, nothing keeps the Django app from writing
# to the tracking database directly, which would be magnitudes faster.

import logging
from datetime import datetime

from crawlerdetect import CrawlerDetect
from django.conf import settings
from huey.contrib.djhuey import task

from lemarche.stats.models import Tracker
from lemarche.users.models import User


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

crawler_detect = CrawlerDetect()


VERSION = 2

TRACKER_IGNORE_LIST = [
    "/static",
    "/favicon.ico",
    "/admin",
    "/select2",
    "/api/perimeters/autocomplete",
    "/track",  # avoid duplicate tracking
]

DEFAULT_PAYLOAD = {
    "version": VERSION,
    "date_created": datetime.now().astimezone().isoformat(),
    "env": settings.BITOUBI_ENV,
    "page": "",
    "action": "load",
    "data": {"source": "bitoubi_api"},  # needs to be stringifyed...
    "session_id": "00000000-1111-2222-aaaa-444444444444",
    "send_order": 0,  # why we use it ?
    "source": "tracker",  # why we use it ?
}


def extract_meta_from_request(request, siae=None, results_count=None):
    user: User = request.user
    return {
        **request.GET,
        "is_admin": user.id and user.kind == User.KIND_ADMIN,
        "user_type": user.kind if user.id else "",
        "user_id": user.id if user.id else None,
        "siae_id": siae.id if siae else None,
        "results_count": results_count,
        "token": request.GET.get("token", ""),
        "cmp": request.GET.get("cmp", ""),
    }


@task()
def track(page: str = "", action: str = "load", meta: dict = {}):  # noqa B006

    # Don't log in dev
    if settings.BITOUBI_ENV != "dev":
        date_created = datetime.now().isoformat()
        # meta_data = DEFAULT_PAYLOAD["data"] | meta
        set_payload = {
            "date_created": date_created,
            "page": page,
            "action": action,
            "data": {
                "_v": 1,
                "env": settings.BITOUBI_ENV,  # est-ce vraiment utile ?
                "meta": DEFAULT_PAYLOAD["data"] | meta,
                "page": page,
                # "order": 0,
                "action": action,
                # "timestamp": date_created,
                # "session_id": "00000000-1111-2222-aaaa-444444444444",
            },
            "isadmin": meta.get("is_admin", False),
        }

        payload = DEFAULT_PAYLOAD | set_payload

        try:
            Tracker.objects.create(**payload)
            logger.info("Tracker saved")
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to save tracker")


class TrackerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        page = request.path
        request_ua = request.META.get("HTTP_USER_AGENT", "")

        # Final checks before calling the track() function
        # - make sure no "ignored" keyword is in the path
        # - make sure the request doesn't come from a crawler
        if all([s not in page for s in TRACKER_IGNORE_LIST]):
            is_crawler = crawler_detect.isCrawler(request_ua)
            if not is_crawler:
                # build meta & co
                results_count = (
                    getattr(response, "context_data", {}).get("paginator").count
                    if getattr(response, "context_data", None)
                    and getattr(response, "context_data", {}).get("paginator")
                    else None
                )
                siae = (
                    getattr(response, "context_data", {}).get("siae", None)
                    if getattr(response, "context_data", None)
                    else None
                )
                meta = extract_meta_from_request(request, siae=siae, results_count=results_count)
                track(
                    page=page,
                    action="load",
                    meta=meta,
                )

        return response
