from django.db import models
from django.utils import timezone


class Datum(models.Model):
    """Store an aggregated `value` of the `code` data point for the specified `bucket`."""

    code = models.TextField()
    bucket = models.TextField(verbose_name="Unique value for the code (for example the date of today)")
    value = models.IntegerField()  # Integer offers the best balance between range, storage size, and performance

    measured_at = models.DateTimeField(default=timezone.now)  # Not using auto_now_add=True to allow overrides

    class Meta:
        verbose_name_plural = "data"
        unique_together = ["code", "bucket"]
        indexes = [models.Index(fields=["measured_at", "code"])]

    def __str__(self) -> str:
        return f"{self.code}({self.bucket}) : {self.value}"
