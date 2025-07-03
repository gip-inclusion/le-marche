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

    def get_user_fields(self, **kwargs) -> dict:
        return {
            "partner_kind": user_constants.PARTNER_KIND_FACILITATOR,
        }

    def get_update_fields(self, **kwargs) -> dict:
        return False
