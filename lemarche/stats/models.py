from datetime import timedelta

from django.db import models
from django.utils import timezone

from lemarche.siaes import constants as siae_constants
from lemarche.users import constants as user_constants


class TrackerQuerySet(models.QuerySet):
    def env_prod(self):
        return self.filter(env="prod", isadmin=False)

    def by_user_kind(self, user_kind):
        return self.filter(user_kind=user_kind)

    def siae_views_last_3_months(self, siae_slug):
        return self.env_prod().filter(
            action="load",
            page=f"/prestataires/{siae_slug}/",
            date_created__gte=timezone.now() - timedelta(days=90),
        )

    def siae_buyer_views_last_3_months(self, siae_slug):
        return self.env_prod().siae_views_last_3_months(siae_slug).by_user_kind(user_constants.KIND_BUYER)

    def siae_partner_views_last_3_months(self, siae_slug):
        return self.env_prod().siae_views_last_3_months(siae_slug).by_user_kind(user_constants.KIND_PARTNER)


class Tracker(models.Model):
    id_internal = models.AutoField(primary_key=True)

    version = models.PositiveIntegerField(verbose_name="Version")
    date_created = models.DateTimeField(verbose_name="Timestamp (UNIX Epoch)")
    env = models.CharField(max_length=200)
    source = models.CharField(max_length=200)

    page = models.CharField(max_length=200)
    action = models.CharField(verbose_name="Type d'action", max_length=200)
    data = models.JSONField()

    user_id = models.IntegerField(blank=True, null=True)
    user_kind = models.CharField(max_length=20, choices=user_constants.KIND_CHOICES_WITH_ADMIN, blank=True)
    isadmin = models.BooleanField(default=False)  # user.kind == User.KIND_ADMIN

    siae_id = models.IntegerField(blank=True, null=True)
    siae_kind = models.CharField(max_length=6, choices=siae_constants.KIND_CHOICES_WITH_EXTRA, blank=True)
    siae_contact_email = models.EmailField(blank=True)

    objects = models.Manager.from_queryset(TrackerQuerySet)()

    class Meta:
        db_table = "trackers"
