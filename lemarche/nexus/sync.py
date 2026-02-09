import logging

from django.conf import settings
from itoutils.django.nexus.api import NexusAPIClient, NexusAPIException

from lemarche.utils.urls import get_object_share_url


logger = logging.getLogger(__name__)


USER_TRACKED_FIELDS = [
    "id",
    "kind",
    "first_name",
    "last_name",
    "email",
    "last_login",
    "is_active",
]


def serialize_user(user):
    return {
        "id": str(user.pk),
        "kind": user.kind,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": "",
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "auth": "DJANGO",
    }


def sync_users(users):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().send_users([serialize_user(user) for user in users])
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to sync users")


def delete_users(user_pks):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().delete_users(user_pks)
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to delete users")


SIAE_TRACKED_FIELDS = [
    "kind",
    "siret",
    "brand",
    "name",
    "phone",
    "email",
    "address",
    "post_code",
    "city",
    "department",
    "website",
    "description",
    "is_active",
    "is_delisted",
]


def serialize_siae(siae):
    return {
        "id": str(siae.pk),
        "kind": siae.kind,
        "siret": siae.siret,
        "name": siae.name_display,
        "phone": siae.phone,
        "email": siae.email,
        "address_line_1": siae.address,
        "address_line_2": "",
        "post_code": siae.post_code,
        "city": siae.city,
        "department": siae.department,
        "website": siae.website,
        "opening_hours": "",
        "accessibility": "",
        "description": siae.description,
        "source_link": get_object_share_url(siae),
    }


def sync_siaes(siaes):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().send_structures([serialize_siae(siae) for siae in siaes])
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to sync siaes")


def delete_siaes(siae_pks):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().delete_structures(siae_pks)
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to delete siaes")


SIAEUSER_TRACKED_FIELDS = [
    "user_id",
    "siae_id",
]


def serialize_membership(siaeuser):
    return {
        "id": str(siaeuser.pk),
        "user_id": str(siaeuser.user_id),
        "structure_id": str(siaeuser.siae_id),
        "role": "ADMINISTRATOR",
    }


def sync_siaeusers(siaeusers):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().send_memberships([serialize_membership(siaeuser) for siaeuser in siaeusers])
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to sync siaeusers")


def delete_siaeusers(siaeuser_pks):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().delete_memberships(siaeuser_pks)
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to delete siaeusers")
