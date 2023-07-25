from uuid import uuid4

from django.db import models
from django.utils import timezone


class ConversationQuerySet(models.QuerySet):
    pass


class Conversation(models.Model):
    KIND_SEARCH = "SEARCH"
    KIND_TENDER = "TENDER"
    KIND_CHOICES = (
        (KIND_SEARCH, "Recherche"),
        (KIND_TENDER, "Dépôt de besoin"),
    )

    uuid = models.UUIDField(verbose_name="Identifiant UUID", default=uuid4, editable=False, unique=True, db_index=True)
    version = models.PositiveIntegerField(verbose_name="Version", default=0)

    kind = models.CharField(
        verbose_name="Type de conversation", default=KIND_SEARCH, choices=KIND_CHOICES, max_length=10, db_index=True
    )

    siae = models.ForeignKey(
        "siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE, null=True, related_name="conversations"
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    data = models.JSONField()

    objects = models.Manager.from_queryset(ConversationQuerySet)()
