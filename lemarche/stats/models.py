from django.db import models


class Tracker(models.Model):
    id_internal = models.AutoField(primary_key=True)

    version = models.PositiveIntegerField(verbose_name="Version")
    date_created = models.DateTimeField(verbose_name="Timestamp (UNIX Epoch)")
    send_order = models.PositiveIntegerField(default=0)
    env = models.CharField(max_length=200)
    source = models.CharField(max_length=200)

    session_id = models.UUIDField(verbose_name="browser session UUID")
    page = models.CharField(max_length=200)
    action = models.CharField(verbose_name="Type d'action", max_length=200)
    data = models.JSONField()
    isadmin = models.BooleanField(default=False)

    class Meta:
        db_table = "trackers"
