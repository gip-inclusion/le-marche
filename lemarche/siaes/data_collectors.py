import datetime
import logging

from django.db import IntegrityError, models, transaction
from django.utils import timezone

from lemarche.analytics.data_collectors import DataCollector
from lemarche.analytics.models import Datum
from lemarche.siaes.models import Siae


logger = logging.getLogger(__name__)


#
class SiaeDatumCode(models.TextChoices):
    # Siae record - Base
    SIAE_RECORD_COMPLETION_COUNT = "SIAE-completions", "SIAE completion"


class SiaeDataCollector(DataCollector):
    def collect_and_save_data(self, before=None, save=True):
        data = [
            {
                "kind": DataCollector.KIND_GLOBAL,
                "code": SiaeDatumCode.SIAE_RECORD_COMPLETION_COUNT,
                "value": Siae.objects.is_live().get_avg_of_field("completion_rate"),
            }
        ]
        if not before:
            before = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

        bucket = (before.date() - datetime.timedelta(days=1)).isoformat()

        for entry in data:
            kind_data = entry.get("kind")
            if kind_data == DataCollector.KIND_GLOBAL:
                datum = Datum(
                    code=entry.get("code").value,
                    bucket=bucket,
                    value=entry.get("value"),
                )
                logger.info(f"Try to save {datum}")
                if save:
                    try:
                        with transaction.atomic():
                            datum.save()
                    except IntegrityError:
                        logger.error(f"Failed to save {datum} because it already exists.")
                    else:
                        logger.info(f"Successfully saved {datum}.")
