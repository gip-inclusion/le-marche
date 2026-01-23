from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.management.base_update_api import UpdateAPICommand
from lemarche.utils.apis.api_zrr import IS_ZRR_KEY, ZRR_CODE_KEY, ZRR_NAME_KEY, get_default_client, is_in_zrr


class Command(UpdateAPICommand):
    """
    Populates API ZRR

    Note: Only on Siae who have coords, filter only on Siae not updated by the API since a two months

    Usage: ./manage.py update_api_zrr_fields
    Usage: ./manage.py update_api_zrr_fields --limit 10
    Usage: ./manage.py update_api_zrr_fields --force
    Usage: ./manage.py update_api_zrr_fields --limit 100 --no-force
    """

    API_NAME = "ZRR"
    FIELDS_TO_BULK_UPDATE = ["is_zrr", "api_zrr_last_sync_date", "zrr_code", "zrr_name"]
    CLIENT = get_default_client()

    @staticmethod
    def get_filter_query(date_limit) -> Q:
        return Q(api_zrr_last_sync_date__lte=date_limit) | Q(api_zrr_last_sync_date__isnull=True)

    @staticmethod
    def is_in_target(latitude, longitude, client):
        return is_in_zrr(latitude, longitude, client=client)

    def update_siae(self, siae):
        # call api is in zrr
        result_is_in_zrr = self.is_in_target(siae.latitude, siae.longitude, client=self.CLIENT)
        self.success_count["etablissement"] += 1
        siae.is_zrr = result_is_in_zrr[IS_ZRR_KEY]
        siae.api_zrr_last_sync_date = timezone.now()
        if siae.is_zrr:
            siae.zrr_code = result_is_in_zrr[ZRR_CODE_KEY]
            siae.zrr_name = result_is_in_zrr[ZRR_NAME_KEY]
            self.success_count["etablissement_target"] += 1
        else:
            siae.zrr_code = ""
            siae.zrr_name = ""
        return siae
