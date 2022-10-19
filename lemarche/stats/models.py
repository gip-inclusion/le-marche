from django.db import models


class Tracker(models.Model):
    id_internal = models.AutoField(primary_key=True)

    version = models.PositiveIntegerField(verbose_name="Version")
    date_created = models.DateTimeField(verbose_name="Timestamp (UNIX Epoch)")
    send_order = models.PositiveIntegerField(default=0)
    env = models.CharField(max_length=200)
    source = models.CharField(max_length=200)

    page = models.CharField(max_length=200)
    action = models.CharField(verbose_name="Type d'action", max_length=200)
    data = models.JSONField()
    isadmin = models.BooleanField(default=False)

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
