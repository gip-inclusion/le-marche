from datetime import datetime, timedelta

from django.db import models

from lemarche.utils import constants


class TrackerQuerySet(models.QuerySet):
    def env_prod(self):
        return self.filter(env="prod", isadmin=False)

    def by_user_type(self, user_type):
        return self.filter(data__meta__user_type=user_type)

    def siae_views_last_3_months(self, siae_slug):
        return self.env_prod().filter(
            action="load",
            page=f"/prestataires/{siae_slug}/",
            date_created__gte=datetime.now() - timedelta(days=90),
        )

    def siae_buyer_views_last_3_months(self, siae_slug):
        return self.env_prod().siae_views_last_3_months(siae_slug).by_user_type("BUYER")

    def siae_partner_views_last_3_months(self, siae_slug):
        return self.env_prod().siae_views_last_3_months(siae_slug).by_user_type("PARTNER")


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
    user_kind = models.CharField(max_length=20, choices=constants.USER_KIND_CHOICES_WITH_ADMIN, blank=True)
    isadmin = models.BooleanField(default=False)  # user.kind == User.KIND_ADMIN

    objects = models.Manager.from_queryset(TrackerQuerySet)()

    class Meta:
        db_table = "trackers"


class StatsUser(models.Model):
    id = models.PositiveIntegerField(
        primary_key=True, auto_created=False, verbose_name="ID app leMarche", db_index=True
    )
    email = models.EmailField(verbose_name="Adresse e-mail", unique=True)
    first_name = models.CharField(verbose_name="Prénom", max_length=150)
    last_name = models.CharField(verbose_name="Nom", max_length=150)
    kind = models.CharField(verbose_name="Type d'utilisateur", max_length=20, blank=True)
    phone = models.CharField(verbose_name="Téléphone", max_length=20, blank=True)
    company_name = models.CharField(verbose_name="Nom de l'entreprise", max_length=255, blank=True)
    position = models.CharField(verbose_name="Poste", max_length=255, blank=True)
    partner_kind = models.CharField(verbose_name="Type de partenaire", max_length=20, blank=True)

    class Meta:
        # avoid "stats_stats_user"
        db_table = "stats_user"
