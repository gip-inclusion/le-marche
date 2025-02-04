from django.db import models
from django.db.models import Count
from django.template.defaultfilters import slugify
from django.utils import timezone
from django_better_admin_arrayfield.models.fields import ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver

from lemarche.utils.constants import ADMIN_FIELD_HELP_TEXT, RECALCULATED_FIELD_HELP_TEXT


class CompanyQuerySet(models.QuerySet):
    def has_user(self):
        return self.filter(users__isnull=False).distinct()

    def has_email_domain(self):
        return self.exclude(email_domain_list=[])

    def with_user_stats(self):
        return self.annotate(user_count_annotated=Count("users", distinct=True)).annotate(
            user_tender_count_annotated=Count("users__tenders", distinct=True)
        )


class Company(models.Model):
    FIELDS_STATS_COUNT = ["user_count", "user_tender_count"]
    FIELDS_STATS_TIMESTAMPS = ["created_at", "updated_at"]
    READONLY_FIELDS = FIELDS_STATS_COUNT + FIELDS_STATS_TIMESTAMPS

    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    description = models.TextField(verbose_name="Description", blank=True)
    siret = models.CharField(verbose_name="Siret", max_length=14, blank=True)
    website = models.URLField(verbose_name="Site web", blank=True)
    logo_url = models.URLField(verbose_name="Lien vers le logo", max_length=500, blank=True)

    email_domain_list = ArrayField(
        verbose_name="Liste des noms de domaine d'e-mails",
        help_text="@entreprise.fr (sans le @)",
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    # stats
    linkedin_buyer_count = models.IntegerField(
        "Nombre d'acheteurs sur LinkedIn", help_text=ADMIN_FIELD_HELP_TEXT, default=0
    )
    user_count = models.IntegerField("Nombre d'utilisateurs", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0)
    user_tender_count = models.IntegerField(
        "Nombre de besoins déposés par les utilisateurs", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    brevo_company_id = models.IntegerField(
        verbose_name="ID Brevo",
        help_text="Identifiant de l'entreprise dans Brevo",
        blank=True,
        null=True,
    )

    objects = models.Manager.from_queryset(CompanyQuerySet)()

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

    def __str__(self):
        return self.name

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = slugify(self.name)[:50]

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)


@receiver(post_save, sender=Company)
def create_company_in_brevo(sender, instance, created, **kwargs):
    if created:
        from lemarche.utils.apis.api_brevo import create_company

        create_company(instance)
