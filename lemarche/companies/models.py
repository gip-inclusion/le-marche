from django.db import models
from django.db.models import Count
from django.template.defaultfilters import slugify
from django.utils import timezone
from django_better_admin_arrayfield.models.fields import ArrayField

from lemarche.utils.constants import ADMIN_FIELD_HELP_TEXT, RECALCULATED_FIELD_HELP_TEXT


class CompanyLabel(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    logo_url = models.URLField(verbose_name="Lien vers le logo", max_length=500)

    class Meta:
        verbose_name = "Label"
        verbose_name_plural = "Labels"

    def __str__(self):
        return self.name


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
    labels = models.ManyToManyField(CompanyLabel, verbose_name="Labels", blank=True)

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

    # Brevo CRM integration
    brevo_company_id = models.CharField(verbose_name="Brevo company id", max_length=80, blank=True, null=True)
    extra_data = models.JSONField(verbose_name="Données complémentaires", editable=False, default=dict)
    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

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

    @property
    def get_label_sentence_display(self) -> str:
        labels = self.labels.values_list("name", flat=True)
        if "RFAR" in labels and "B-Corp" in labels:
            return (
                "L’organisation de cet acheteur est certifié RFAR et B-Corp,"
                " garantissant son engagement envers des relations fournisseurs responsables et son impact social"
            )
        elif "RFAR" in labels:
            return (
                "L’organisation de cet acheteur est certifié RFAR,"
                " garantissant son engagement envers des relations fournisseurs responsables"
            )
        elif "B-Corp" in labels:
            return "L’organisation de cet acheteur est certifiée B-Corp, garantissant son engagement social"
        else:
            return ""


class CompanySiaeClientReferenceMatch(models.Model):
    """
    Model to store potential matches between Company and SiaeClientReference
    that can be moderated by human admins.
    """

    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "En attente"
        APPROVED = "approved", "Approuvé"
        REJECTED = "rejected", "Rejeté"

    company = models.ForeignKey(
        Company, verbose_name="Entreprise", on_delete=models.CASCADE, related_name="siae_client_reference_matches"
    )
    siae_client_reference = models.OneToOneField(
        "siaes.SiaeClientReference",
        verbose_name="Référence client SIAE",
        on_delete=models.CASCADE,
        related_name="company_matches",
    )

    # Matching algorithm data
    similarity_score = models.DecimalField(
        verbose_name="Score de similarité",
        help_text="Score de similarité trigram entre les noms",
        max_digits=7,
        decimal_places=6,
    )
    company_name = models.CharField(
        verbose_name="Nom de l'entreprise",
        max_length=255,
        help_text="Nom de l'entreprise au moment de la correspondance",
    )
    client_reference_name = models.CharField(
        verbose_name="Nom de la référence client",
        max_length=255,
        help_text="Nom de la référence client au moment de la correspondance",
    )

    # Moderation
    moderation_status = models.CharField(
        verbose_name="Statut de modération",
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )
    moderated_by = models.ForeignKey(
        "users.User",
        verbose_name="Modéré par",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_matches_moderated",
    )
    moderated_at = models.DateTimeField(verbose_name="Date de modération", null=True, blank=True)
    moderation_notes = models.TextField(verbose_name="Notes de modération", blank=True)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Correspondance entreprise-référence client"
        verbose_name_plural = "Correspondances entreprise-référence client"
        unique_together = ["company", "siae_client_reference"]
        ordering = ["-similarity_score", "-created_at"]

    def __str__(self):
        return f"{self.company_name} <-> {self.client_reference_name} ({self.similarity_score:.2f})"
