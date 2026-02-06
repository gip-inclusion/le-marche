import json

from django.utils import timezone

from lemarche.siaes.models import Siae, SiaeUser
from lemarche.users.models import User
from lemarche.utils.urls import get_object_share_url
from tests.siaes.factories import SiaeFactory, SiaeUserFactory
from tests.users.factories import UserFactory


def assert_call_content(call, expected_data):
    # the order doesn't matter
    data = json.loads(call.request.content.decode())
    assert sorted(data, key=lambda d: d["id"]) == sorted(expected_data, key=lambda d: d["id"])


class TestUserSync:
    def test_sync_on_model_save_new_instance(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        with django_capture_on_commit_callbacks(execute=True):
            user = UserFactory()

        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
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

    def test_sync_on_model_save_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user.email = "another@email.com"
            user.last_login = timezone.now()
            user.save()
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
                {
                    "id": str(user.pk),
                    "kind": "SIAE",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": "another@email.com",
                    "phone": "",
                    "last_login": user.last_login.isoformat(),
                    "auth": "DJANGO",
                },
            ],
        )

    def test_no_sync_on_model_save_no_changed_data(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user.save()
        assert mock_nexus_api.calls == []

    def test_no_sync_on_model_save_non_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user.partner_kind = "AUTRE"
            user.save()
        assert mock_nexus_api.calls == []

    def test_delete_on_model_save(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        with django_capture_on_commit_callbacks(execute=True):
            user_1 = UserFactory(is_active=False)
            user_2 = UserFactory(email="")

        [call_1, call_2] = mock_nexus_api.calls
        assert call_1.request.method == "DELETE"
        assert call_1.request.url == "http://nexus/api/users"
        assert json.loads(call_1.request.content.decode()) == [{"id": str(user_1.pk)}]
        assert call_2.request.method == "DELETE"
        assert call_2.request.url == "http://nexus/api/users"
        assert json.loads(call_2.request.content.decode()) == [{"id": str(user_2.pk)}]

    def test_delete_on_model_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()
        user_id = user.pk

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_id)}])

    def test_sync_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            User.objects.order_by("pk").update(first_name="John")
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
                {
                    "id": str(user_1.pk),
                    "kind": "SIAE",
                    "first_name": "John",
                    "last_name": user_1.last_name,
                    "email": user_1.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "DJANGO",
                },
                {
                    "id": str(user_2.pk),
                    "kind": "SIAE",
                    "first_name": "John",
                    "last_name": user_2.last_name,
                    "email": user_2.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "DJANGO",
                },
            ],
        )

    def test_delete_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            User.objects.order_by("pk").update(is_active=False)
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_1.pk)}, {"id": str(user_2.pk)}])

    def test_delete_on_manager_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            User.objects.order_by("pk").delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_1.pk)}, {"id": str(user_2.pk)}])

    def test_sync_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user_1.first_name = "John"
            user_2.first_name = "Not John"
            User.objects.bulk_update([user_1, user_2], ["first_name"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
                {
                    "id": str(user_1.pk),
                    "kind": "SIAE",
                    "first_name": "John",
                    "last_name": user_1.last_name,
                    "email": user_1.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "DJANGO",
                },
                {
                    "id": str(user_2.pk),
                    "kind": "SIAE",
                    "first_name": "Not John",
                    "last_name": user_2.last_name,
                    "email": user_2.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "DJANGO",
                },
            ],
        )

    def test_delete_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user_1.is_active = False
            user_2.is_active = False
            User.objects.bulk_update([user_1, user_2], ["is_active"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_1.pk)}, {"id": str(user_2.pk)}])


class TestSiaeSync:
    def test_sync_on_model_save_new_instance(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        with django_capture_on_commit_callbacks(execute=True):
            siae = SiaeFactory()

        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(
            call,
            [
                {
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
                },
            ],
        )

    def test_sync_on_model_save_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae.email = "another@email.com"
            siae.save()
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae.pk),
                    "kind": siae.kind,
                    "siret": siae.siret,
                    "name": siae.name_display,
                    "phone": siae.phone,
                    "email": "another@email.com",
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
                },
            ],
        )

    def test_no_sync_on_model_save_no_changed_data(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae.save()
        assert mock_nexus_api.calls == []

    def test_no_sync_on_model_save_non_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae.image_name = "img.png"
            siae.save()
        assert mock_nexus_api.calls == []

    def test_delete_on_model_save(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        with django_capture_on_commit_callbacks(execute=True):
            siae_1 = SiaeFactory(is_active=False)
            siae_2 = SiaeFactory(is_delisted=True)

        [call_1, call_2] = mock_nexus_api.calls
        assert call_1.request.method == "DELETE"
        assert call_1.request.url == "http://nexus/api/structures"
        assert json.loads(call_1.request.content.decode()) == [{"id": str(siae_1.pk)}]
        assert call_2.request.method == "DELETE"
        assert call_2.request.url == "http://nexus/api/structures"
        assert json.loads(call_2.request.content.decode()) == [{"id": str(siae_2.pk)}]

    def test_delete_on_model_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae = SiaeFactory()
        siae_id = siae.pk

        with django_capture_on_commit_callbacks(execute=True):
            siae.delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(call, [{"id": str(siae_id)}])

    def test_sync_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            Siae.objects.order_by("pk").update(brand="Monster Inc")
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae_1.pk),
                    "kind": siae_1.kind,
                    "siret": siae_1.siret,
                    "name": "Monster Inc",
                    "phone": siae_1.phone,
                    "email": siae_1.email,
                    "address_line_1": siae_1.address,
                    "address_line_2": "",
                    "post_code": siae_1.post_code,
                    "city": siae_1.city,
                    "department": siae_1.department,
                    "website": siae_1.website,
                    "opening_hours": "",
                    "accessibility": "",
                    "description": siae_1.description,
                    "source_link": get_object_share_url(siae_1),
                },
                {
                    "id": str(siae_2.pk),
                    "kind": siae_2.kind,
                    "siret": siae_2.siret,
                    "name": "Monster Inc",
                    "phone": siae_2.phone,
                    "email": siae_2.email,
                    "address_line_1": siae_2.address,
                    "address_line_2": "",
                    "post_code": siae_2.post_code,
                    "city": siae_2.city,
                    "department": siae_2.department,
                    "website": siae_2.website,
                    "opening_hours": "",
                    "accessibility": "",
                    "description": siae_2.description,
                    "source_link": get_object_share_url(siae_2),
                },
            ],
        )

    def test_delete_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            Siae.objects.order_by("pk").update(is_active=False)
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(call, [{"id": str(siae_1.pk)}, {"id": str(siae_2.pk)}])

    def test_delete_on_manager_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            Siae.objects.order_by("pk").delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(call, [{"id": str(siae_1.pk)}, {"id": str(siae_2.pk)}])

    def test_sync_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_1.brand = "Monster Inc"
            siae_2.brand = "Monster & Cie"
            Siae.objects.bulk_update([siae_1, siae_2], ["brand"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae_1.pk),
                    "kind": siae_1.kind,
                    "siret": siae_1.siret,
                    "name": "Monster Inc",
                    "phone": siae_1.phone,
                    "email": siae_1.email,
                    "address_line_1": siae_1.address,
                    "address_line_2": "",
                    "post_code": siae_1.post_code,
                    "city": siae_1.city,
                    "department": siae_1.department,
                    "website": siae_1.website,
                    "opening_hours": "",
                    "accessibility": "",
                    "description": siae_1.description,
                    "source_link": get_object_share_url(siae_1),
                },
                {
                    "id": str(siae_2.pk),
                    "kind": siae_2.kind,
                    "siret": siae_2.siret,
                    "name": "Monster & Cie",
                    "phone": siae_2.phone,
                    "email": siae_2.email,
                    "address_line_1": siae_2.address,
                    "address_line_2": "",
                    "post_code": siae_2.post_code,
                    "city": siae_2.city,
                    "department": siae_2.department,
                    "website": siae_2.website,
                    "opening_hours": "",
                    "accessibility": "",
                    "description": siae_2.description,
                    "source_link": get_object_share_url(siae_2),
                },
            ],
        )

    def test_delete_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_1.is_active = False
            siae_2.is_active = False
            Siae.objects.bulk_update([siae_1, siae_2], ["is_active"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/structures"
        assert_call_content(call, [{"id": str(siae_1.pk)}, {"id": str(siae_2.pk)}])


class TestSiaeUserSync:
    def test_sync_on_model_save_new_instance(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()
        siae = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user = SiaeUserFactory(user=user, siae=siae)
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae_user.pk),
                    "user_id": str(siae_user.user.pk),
                    "structure_id": str(siae_user.siae.pk),
                    "role": "ADMINISTRATOR",
                },
            ],
        )

    def test_sync_on_model_save_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()
        other_siae = SiaeFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user.siae = other_siae
            siae_user.save()
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae_user.pk),
                    "user_id": str(siae_user.user.pk),
                    "structure_id": str(other_siae.pk),
                    "role": "ADMINISTRATOR",
                },
            ],
        )

    def test_no_sync_on_model_save_no_change(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user.save()
        assert mock_nexus_api.calls == []

    def test_no_sync_on_model_save_non_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user.created_at = timezone.now()
            siae_user.save()
        assert mock_nexus_api.calls == []

    def test_delete_on_model_save(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()
        siae_user.siae.is_active = False
        siae_user.siae.save()
        other_user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user.user = other_user
            siae_user.save()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(call, [{"id": str(siae_user.pk)}])

    def test_sync_on_model_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user_id = siae_user.pk
            siae_user.delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(call, [{"id": str(siae_user_id)}])

    def test_sync_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            SiaeUser.objects.update(user=user_2)
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae_user.pk),
                    "user_id": str(user_2.pk),
                    "structure_id": str(siae_user.siae.pk),
                    "role": "ADMINISTRATOR",
                },
            ],
        )

    def test_delete_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user = SiaeUserFactory()
        inactive_user = UserFactory(is_active=False)

        with django_capture_on_commit_callbacks(execute=True):
            SiaeUser.objects.order_by("pk").update(user=inactive_user)
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(call, [{"id": str(siae_user.pk)}])

    def test_delete_on_manager_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user_1 = SiaeUserFactory()
        siae_user_2 = SiaeUserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            SiaeUser.objects.order_by("pk").delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(call, [{"id": str(siae_user_1.pk)}, {"id": str(siae_user_2.pk)}])

    def test_sync_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user_1 = SiaeUserFactory()
        siae_user_2 = SiaeUserFactory()
        other_user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            siae_user_1.user = other_user
            siae_user_2.user = other_user
            SiaeUser.objects.bulk_update([siae_user_1, siae_user_2], ["user"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(
            call,
            [
                {
                    "id": str(siae_user_1.pk),
                    "user_id": str(other_user.pk),
                    "structure_id": str(siae_user_1.siae.pk),
                    "role": "ADMINISTRATOR",
                },
                {
                    "id": str(siae_user_2.pk),
                    "user_id": str(other_user.pk),
                    "structure_id": str(siae_user_2.siae.pk),
                    "role": "ADMINISTRATOR",
                },
            ],
        )

    def test_delete_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        siae_user_1 = SiaeUserFactory()
        siae_user_2 = SiaeUserFactory()
        inactive_siae = SiaeFactory(is_active=False)

        with django_capture_on_commit_callbacks(execute=True):
            siae_user_1.siae = inactive_siae
            siae_user_2.siae = inactive_siae
            SiaeUser.objects.bulk_update([siae_user_1, siae_user_2], ["siae"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/memberships"
        assert_call_content(call, [{"id": str(siae_user_1.pk)}, {"id": str(siae_user_2.pk)}])
