from itoutils.django.nexus.management.base_full_sync import BaseNexusFullSyncCommand

from lemarche.nexus.sync import serialize_membership, serialize_siae, serialize_user
from lemarche.siaes.models import Siae, SiaeUser
from lemarche.users import constants as user_constants
from lemarche.users.models import User


class Command(BaseNexusFullSyncCommand):
    structure_serializer = staticmethod(serialize_siae)
    user_serializer = staticmethod(serialize_user)
    membership_serializer = staticmethod(serialize_membership)

    def get_structures_queryset(self):
        return Siae.objects.is_live().exclude(siret="").order_by("pk")

    def get_users_queryset(self):
        return (
            User.objects.filter(kind=user_constants.KIND_SIAE, is_active=True)
            .exclude(email="")
            .exclude(email=None)
            .order_by("pk")
        )

    def get_memberships_queryset(self):
        return SiaeUser.objects.filter(
            user__is_active=True,
            siae__is_active=True,
            siae__is_delisted=False,
        ).order_by("pk")
