import uuid

from django.db import models
from django.utils import timezone


class DatumCode(models.TextChoices):
    # Siae record - Base
    SIAE_RECORD_COMPLETION_COUNT = "SIAE-001", "SIAE completion"


class Datum(models.Model):
    """Store an aggregated `value` of the `code` data point for the specified `bucket`."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    code = models.TextField(choices=DatumCode.choices)
    bucket = models.TextField()
    value = models.IntegerField()  # Integer offers the best balance between range, storage size, and performance

    measured_at = models.DateTimeField(default=timezone.now)  # Not using auto_now_add=True to allow overrides

    class Meta:
        verbose_name_plural = "data"
        unique_together = ["code", "bucket"]
        indexes = [models.Index(fields=["measured_at", "code"])]
