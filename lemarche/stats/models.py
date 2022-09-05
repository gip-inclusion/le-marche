from django.db import models


class Tracker(models.Model):

    v = models.PositiveIntegerField(verbose_name="Version")
    timestamp = models.DateTimeField(verbose_name="Timestamp (UNIX Epoch)")
    order = models.PositiveIntegerField()
    env = models.CharField(max_length=200)

    session_id = models.UUIDField(verbose_name="browser session UUID")
    page = models.CharField(max_length=200)
    action = models.CharField(verbose_name="Type d'action", max_length=200)
    meta = models.JSONField()
