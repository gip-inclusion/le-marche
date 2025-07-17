from lemarche.users import constants as user_constants
from lemarche.users.management.commands.base_import_users import BaseImportUsersCommand
from lemarche.users.models import User


class Command(BaseImportUsersCommand):
    """Import new partners from a csv file.
    The file should respect these headers:
        FIRST_NAME | LAST_NAME | EMAIL | PHONE | POSITION
    """

    def get_user_kind(self) -> str:
        return User.KIND_PARTNER

    def get_user_fields(self, imported_user: dict, **kwargs) -> dict:
        user_fields = super().get_user_fields(imported_user, **kwargs)
        user_fields.update({"partner_kind": user_constants.PARTNER_KIND_FACILITATOR})
        return user_fields

    def get_update_fields(self) -> dict:
        return {}
