from django.db.models import Q

from lemarche.siaes.management.base_update_api import UpdateAPICommand
from lemarche.utils.apis.api_zrr import IS_ZRR_KEY, ZRR_CODE_KEY, ZRR_NAME_KEY, get_default_client, is_in_zrr


class Command(UpdateAPICommand):
    """
    Populates API ZRR

    Note: Only on Siae who have coords, filter only on Siae not updated by the API since a two months

    Usage: poetry run python manage.py update_api_zrr_fields
    Usage: poetry run python manage.py update_api_zrr_fields --limit 10
    Usage: poetry run python manage.py update_api_zrr_fields --force
    Usage: poetry run python manage.py update_api_zrr_fields --limit 100 --no-force
    """

    API_NAME = "ZRR"
    FIELDS_TO_BULK_UPDATE = ["is_zrr", "api_zrr_last_sync_date", "zrr_code", "zrr_name"]
    CLIENT = get_default_client()

    IS_TARGET_KEY = IS_ZRR_KEY
    TARGET_CODE_KEY = ZRR_CODE_KEY
    TARGET_NAME_KEY = ZRR_NAME_KEY

    @staticmethod
    def get_filter_query(date_limit) -> Q:
        return Q(api_zrr_last_sync_date__lte=date_limit) | Q(api_zrr_last_sync_date__isnull=True)

    @staticmethod
    def is_in_target(latitude, longitude, client):
        return is_in_zrr(latitude, longitude, client=client)
