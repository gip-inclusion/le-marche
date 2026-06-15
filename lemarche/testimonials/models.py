import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from lemarche.testimonials import constants as testimonial_constants


class SiaeTestimonialQuerySet(models.QuerySet):
    def is_sent(self):
        return self.filter(status=testimonial_constants.STATUS_SENT)

    def is_submitted(self):
        return self.filter(status=testimonial_constants.STATUS_SUBMITTED)

    def is_published(self):
        return self.filter(status=testimonial_constants.STATUS_PUBLISHED)

    def is_rejected(self):
        return self.filter(status=testimonial_constants.STATUS_REJECTED)

    def filter_by_siae(self, siae):
        return self.filter(siae=siae)

    def sent_this_week(self, siae):
        week_ago = timezone.now() - timedelta(days=7)
        return self.filter(siae=siae, sent_at__gte=week_ago)


class SiaeTestimonial(models.Model):
    siae = models.ForeignKey(
        "siaes.Siae",
        verbose_name="Structure",
        on_delete=models.CASCADE,
        related_name="testimonials",
    )
    client_email = models.EmailField(verbose_name="Email du client")
    custom_message = models.TextField(verbose_name="Message personnalisé", blank=True)

    token = models.UUIDField(
        verbose_name="Token",
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        editable=False,
    )
    sent_at = models.DateTimeField(verbose_name="Date d'envoi", null=True, blank=True)
    token_expires_at = models.DateTimeField(verbose_name="Date d'expiration du token", null=True, blank=True)

    content = models.TextField(
        verbose_name="Témoignage",
        blank=True,
        max_length=testimonial_constants.CONTENT_MAX_LENGTH,
    )
    author_first_name = models.CharField(verbose_name="Prénom de l'auteur", max_length=255, blank=True)
    author_last_name = models.CharField(verbose_name="Nom de l'auteur", max_length=255, blank=True)
    author_organization = models.CharField(verbose_name="Organisation de l'auteur", max_length=100, blank=True)

    buyer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur acheteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials_given",
    )

    submitted_at = models.DateTimeField(verbose_name="Date de soumission", null=True, blank=True)
    published_at = models.DateTimeField(verbose_name="Date de publication", null=True, blank=True)

    status = models.CharField(
        verbose_name="Statut",
        max_length=20,
        choices=testimonial_constants.STATUS_CHOICES,
        default=testimonial_constants.STATUS_SENT,
        db_index=True,
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(SiaeTestimonialQuerySet)()

    class Meta:
        verbose_name = "Témoignage client"
        verbose_name_plural = "Témoignages clients"
        unique_together = ("siae", "client_email")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Témoignage de {self.client_email} pour {self.siae.name}"

    @property
    def is_token_valid(self) -> bool:
        """Vérifie que le token n'est pas expiré."""
        if not self.token_expires_at:
            return False
        return timezone.now() < self.token_expires_at

    @property
    def author_display_name(self) -> str:
        """Retourne le prénom et nom d'affichage de l'auteur."""
        parts = [self.author_first_name, self.author_last_name]
        return " ".join(p for p in parts if p).strip()

    def publish(self) -> None:
        """Publie le témoignage."""
        self.status = testimonial_constants.STATUS_PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def reject(self) -> None:
        """Rejette le témoignage."""
        self.status = testimonial_constants.STATUS_REJECTED
        self.save(update_fields=["status", "updated_at"])
