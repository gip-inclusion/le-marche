import datetime
import logging

from django.db import IntegrityError, models, transaction
from django.utils import timezone

from lemarche.analytics.data_collectors import DataCollector
from lemarche.analytics.models import Datum
from lemarche.siaes.models import Siae


logger = logging.getLogger(__name__)


#
class DatumCode(models.TextChoices):
    # Siae record - Base
    SIAE_RECORD_COMPLETION_COUNT = "SIAE-completions", "SIAE completion"


class SiaeDataCollector(DataCollector):
    def collect_data(self, before=None):
        # Collect data for Model A
        data = {
            DatumCode.SIAE_RECORD_COMPLETION_COUNT: Siae.objects.is_live()
            .aggregate(completetion_avg=models.Avg("completion_rate"))
            .get("completetion_avg"),
        }
        if not before:
            before = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

        bucket = (before.date() - datetime.timedelta(days=1)).isoformat()

        for code, value in data.items():
            datum = Datum(
                code=code.value,
                bucket=bucket,
                value=value,
            )
            try:
                with transaction.atomic():
                    datum.save()
            except IntegrityError:
                logger.error(f"Failed to save code={code.value} for bucket={bucket} because it already exists.")
            else:
                logger.info(f"Successfully saved code={code.value} bucket={bucket} value={value}.")
