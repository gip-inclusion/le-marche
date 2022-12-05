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

from crawlerdetect import CrawlerDetect
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone

from lemarche.stats.models import Tracker
from lemarche.users.models import User


# from huey.contrib.djhuey import task


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

crawler_detect = CrawlerDetect()


VERSION = 3

TRACKER_IGNORE_LIST = [
    "/static",
    "/favicon.ico",
    "/admin",
    "/select2",
    "/api/perimeters/autocomplete",
    "/media",
    "/track",  # avoid duplicate tracking
]

DEFAULT_PAYLOAD = {
    "version": VERSION,
    "env": settings.BITOUBI_ENV,
    "data": {"source": "bitoubi_api"},  # needs to be stringifyed...
    "source": "tracker",  # why we use it ?
}


# @task()
def track(page: str = "", action: str = "load", meta: dict = {}):  # noqa B006

    # Don't log in dev
    if settings.BITOUBI_ENV not in ("test"):
        date_created = timezone.now()
        set_payload = {
            "date_created": date_created,
            "page": page,
            "action": action,
            "data": {
                # need to be removed later, because we need complete migration
                "meta": DEFAULT_PAYLOAD["data"]
                | meta,
            },
            "user_id": int(meta.get("user_id")) if meta.get("user_id", None) else None,
            "user_kind": meta.get("user_type") if meta.get("user_type", "") else "",
            "isadmin": meta.get("is_admin", False),
            "siae_id": int(meta.get("siae_id")) if meta.get("siae_id", None) else None,
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

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        page = request.path
        if self.tracking_this_page(page, request):
            self.track_page(page, request, response)
        return response

    def tracking_this_page(self, page, request: HttpRequest) -> bool:
        request_ua = request.META.get("HTTP_USER_AGENT", "")
        # Final checks before calling the track() function
        # - make sure no "ignored" keyword is in the path
        # - make sure the request doesn't come from a crawler
        if all([s not in page for s in TRACKER_IGNORE_LIST]):
            is_crawler = crawler_detect.isCrawler(request_ua)
            return not is_crawler
        return False

    def track_page(self, page, request: HttpRequest, response: HttpResponse):
        action = "load"
        meta = None

        if request.method == "GET":
            context_data = self.get_context_data(response)
            if page == (reverse("siae:search_results")):  # Search action
                action = "directory_search"
                extra_data = {
                    "results_count": context_data.get("paginator").count if context_data.get("paginator") else None
                }
                meta = self.extract_meta_from_request_get(request, context_data=context_data, extra_data=extra_data)

            elif page == reverse("siae:search_results_download"):  # download csv action
                action = "directory_csv"
                extra_data = {
                    "results_count": int(response.headers.get("Context-Data-Results-Count"))
                    if response.headers.get("Context-Data-Results-Count", None)
                    else None
                }
                meta = self.extract_meta_from_request_get(request, context_data=context_data, extra_data=extra_data)

            elif page == reverse("dashboard:siae_search_by_siret"):  # adopted search action
                action = "adopt_search"
                meta = self.extract_meta_from_request_get(request, context_data=context_data)

            else:
                meta = self.extract_meta_from_request_get(request, context_data=context_data)

        if meta:
            track(
                page=page,
                action=action,
                meta=meta,
            )

    def extract_user_info(self, request: HttpRequest, context_data: dict):
        user: User = request.user
        siae = context_data.get("siae")
        return {
            "user_id": user.id if user.is_authenticated else None,
            "user_type": user.kind if user.is_authenticated else "",
            "is_admin": user.is_authenticated and user.kind == User.KIND_ADMIN,
            "siae_id": siae.id if siae else None,
        }

    def get_context_data(self, response: HttpResponse):
        context_data = getattr(response, "context_data", {})
        context_data = context_data if context_data else {}
        return context_data

    def extract_meta_from_request_get(self, request: HttpRequest, context_data: dict, extra_data: dict = {}):
        user_info: dict = self.extract_user_info(request, context_data)
        return user_info | request.GET | extra_data

    def extract_meta_from_request_post(
        self, request: HttpRequest, context_data: dict, extract_data=False, remove_items: tuple = ()
    ) -> dict:
        """Extract data from POST request

        Args:
            request (HttpRequest): Current request
            context_data (context_data): Current context_data
            extract_data (bool, optional): If True, extract the data from request. Defaults to False.
            remove_items (tuple, optional): Tuple of keys to remove from the data POST. Defaults to ().

        Returns:
            dict: extracted data from the request
        """
        user_info: dict = self.extract_user_info(request, context_data)
        if extract_data:
            data_post = dict(request.POST)
            for key in remove_items + ("csrfmiddlewaretoken",):
                data_post.pop(key)
            return user_info | data_post
        return user_info
