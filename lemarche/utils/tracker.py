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
from django.utils import timezone

from lemarche.stats.models import Tracker


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


def track(page: str = "", action: str = "load", meta: dict = {}):  # noqa B006
    # Don't log in dev
    if settings.BITOUBI_ENV not in ("dev", "test"):
        date_created = timezone.now()
        user_id = meta.get("user_id", None)
        if user_id:
            user_id = int(user_id[0]) if (type(user_id) is list) else int(user_id)
        user_kind = meta.get("user_kind") if meta.get("user_kind", "") else ""
        siae_id = meta.get("siae_id", None)
        if siae_id:
            if type(siae_id) is list:
                if siae_id[0]:
                    siae_id = int(siae_id[0])
                else:
                    siae_id = None
            else:
                siae_id = int(siae_id)

        siae_kind = meta.get("siae_kind") if meta.get("siae_kind", "") else ""
        siae_contact_email = meta.get("siae_contact_email") if meta.get("siae_contact_email", "") else ""

        set_payload = {
            "date_created": date_created,
            "page": page,
            "action": action,
            "data": {
                # need to be removed later, because we need complete migration
                "meta": DEFAULT_PAYLOAD["data"]
                | meta,
            },
            "user_id": user_id,
            "user_kind": user_kind,
            "isadmin": meta.get("is_admin", False),
            "siae_id": siae_id,
            "siae_kind": siae_kind,
            "siae_contact_email": siae_contact_email,
        }
        payload = DEFAULT_PAYLOAD | set_payload

        try:
            Tracker.objects.create(**payload)
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to save tracker")
