from django.conf import settings
from django.db import models
from django.db.models import Func, IntegerField
from django.utils import timezone
from django_extensions.db.fields import ShortUUIDField
from shortuuid import uuid


class ConversationQuerySet(models.QuerySet):
    def has_answer(self):
        return self.exclude(data=[])

    def with_answer_count(self):
        return self.annotate(answer_count=Func("data", function="jsonb_array_length", output_field=IntegerField()))


class Conversation(models.Model):
    KIND_SEARCH = "SEARCH"
    KIND_TENDER = "TENDER"
    KIND_CHOICES = (
        (KIND_SEARCH, "Recherche"),
        (KIND_TENDER, "Dépôt de besoin"),
    )

    USER_KIND_SENDER_TO_BUYER = "b"
    USER_KIND_SENDER_TO_SIAE = "s"

    uuid = ShortUUIDField(
        verbose_name="Identifiant UUID",
        default=uuid,
        editable=False,
        unique=True,
        db_index=True,
        auto_created=True,
    )

    version = models.PositiveIntegerField(verbose_name="Version", default=0)

    kind = models.CharField(
        verbose_name="Type de conversation", default=KIND_SEARCH, choices=KIND_CHOICES, max_length=10, db_index=True
    )
    sender_email = models.EmailField(verbose_name="Email de l'initiateur de la conversation", null=True)
    sender_first_name = models.CharField(verbose_name="Prénom", max_length=150)
    sender_last_name = models.CharField(verbose_name="Nom", max_length=150)

    title = models.CharField(verbose_name="Objet de la première demande", max_length=200)
    initial_body_message = models.TextField(verbose_name="Message initial", blank=True)
    siae = models.ForeignKey(
        "siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE, null=True, related_name="conversations"
    )

    data = models.JSONField(default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(ConversationQuerySet)()

    class Meta:
        verbose_name = "Conversation"

    def __str__(self):
        return self.title

    @property
    def sender_email_buyer(self):
        return self.sender_email

    @property
    def sender_email_buyer_encoded(self):
        return f"{self.uuid}_{self.USER_KIND_SENDER_TO_BUYER}@{settings.INBOUND_PARSING_DOMAIN_EMAIL}"

    @property
    def sender_email_siae_encoded(self):
        return f"{self.uuid}_{self.USER_KIND_SENDER_TO_SIAE}@{settings.INBOUND_PARSING_DOMAIN_EMAIL}"

    @property
    def sender_email_siae(self):
        return self.siae.contact_email

    @staticmethod
    def get_email_info_from_address(address_mail: str) -> list:
        """Extract info from address mail managed by this class
        Args:
            address_mail (str): _description_

        Returns:
            [UUID, KIND_SENDER]
        """
        return address_mail.split("@")[0].split("_")
