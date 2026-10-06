import json

from django.core.management import call_command
from freezegun import freeze_time
from itoutils.django.testing import assertSnapshotQueries

from lemarche.users.models import User
from lemarche.utils.urls import get_object_share_url
from tests.siaes.factories import SiaeFactory, SiaeUserFactory
from tests.users.factories import UserFactory


def assert_call_content(call, expected_data):
    # the order doesn't matter
    data = json.loads(call.request.content.decode())
    assert sorted(data, key=lambda d: d["id"]) == sorted(expected_data, key=lambda d: d["id"])


@freeze_time()
def test_full_sync(db, mock_nexus_api, snapshot):
    user = UserFactory()
    siae_1 = SiaeFactory()
    siae_2 = SiaeFactory()
    siaeuser_1 = SiaeUserFactory(user=user, siae=siae_1)
    siaeuser_2 = SiaeUserFactory(user=user, siae=siae_2)

    # ignored users
    UserFactory(kind=User.KIND_ADMIN)
    UserFactory(kind=User.KIND_BUYER)
    UserFactory(kind=User.KIND_PARTNER)
    UserFactory(kind=User.KIND_INDIVIDUAL)
    # Ignored mempberships, users, and siaes
    SiaeUserFactory(user=user, siae__is_active=False)
    SiaeUserFactory(user=user, siae__is_delisted=True)
    SiaeUserFactory(user__is_active=False, siae=siae_1)

    mock_nexus_api.reset()

    with assertSnapshotQueries(snapshot):
        call_command("nexus_full_sync")

    [call_init, call_sync_structures, call_sync_users, call_sync_memberships, call_completed] = mock_nexus_api.calls

    assert call_init.request.method == "POST"
    assert call_init.request.url == "http://nexus/api/sync-start"
    started_at = call_init.response.json()["started_at"]

    assert call_sync_structures.request.method == "POST"
    assert call_sync_structures.request.url == "http://nexus/api/structures"
    assert_call_content(
        call_sync_structures,
        [
            {
                "id": str(siae_1.pk),
                "kind": siae_1.kind,
                "siret": siae_1.siret,
                "name": siae_1.name_display,
                "phone": siae_1.phone,
                "email": siae_1.email,
                "address_line_1": siae_1.address,
                "address_line_2": "",
                "post_code": siae_1.post_code,
                "city": siae_1.city,
                "department": siae_1.department,
                "accessibility": "",
                "description": siae_1.description,
                "opening_hours": "",
                "source_link": get_object_share_url(siae_1),
                "website": "",
            },
            {
                "id": str(siae_2.pk),
                "kind": siae_2.kind,
                "siret": siae_2.siret,
                "name": siae_2.name_display,
                "phone": siae_2.phone,
                "email": siae_2.email,
                "address_line_1": siae_2.address,
                "address_line_2": "",
                "post_code": siae_2.post_code,
                "city": siae_2.city,
                "department": siae_2.department,
                "accessibility": "",
                "description": siae_2.description,
                "opening_hours": "",
                "source_link": get_object_share_url(siae_2),
                "website": "",
            },
        ],
    )

    assert call_sync_users.request.method == "POST"
    assert call_sync_users.request.url == "http://nexus/api/users"
    assert_call_content(
        call_sync_users,
        [
            {
                "id": str(user.pk),
                "kind": "SIAE",
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": "",
                "last_login": None,
                "auth": "DJANGO",
            },
        ],
    )

    assert call_sync_memberships.request.method == "POST"
    assert call_sync_memberships.request.url == "http://nexus/api/memberships"
    assert_call_content(
        call_sync_memberships,
        [
            {
                "id": str(siaeuser_1.pk),
                "user_id": str(user.pk),
                "structure_id": str(siae_1.pk),
                "role": "ADMINISTRATOR",
            },
            {
                "id": str(siaeuser_2.pk),
                "user_id": str(user.pk),
                "structure_id": str(siae_2.pk),
                "role": "ADMINISTRATOR",
            },
        ],
    )

    assert call_completed.request.method == "POST"
    assert call_completed.request.url == "http://nexus/api/sync-completed"
    assert json.loads(call_completed.request.content.decode()) == {"started_at": started_at}
