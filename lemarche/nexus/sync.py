import logging

from lemarche.utils.urls import get_object_share_url


logger = logging.getLogger(__name__)


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


def serialize_membership(siaeuser):
    return {
        "id": str(siaeuser.pk),
        "user_id": str(siaeuser.user_id),
        "structure_id": str(siaeuser.siae_id),
        "role": "ADMINISTRATOR",
    }
