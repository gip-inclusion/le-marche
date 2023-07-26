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
    title = models.CharField(verbose_name="Titre de la conversation", max_length=200)
    siae = models.ForeignKey(
        "siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE, null=True, related_name="conversations"
    )
    email_sender = models.EmailField(verbose_name="Email de l'intitiateur de la conversation", null=True)

    data = models.JSONField(default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(ConversationQuerySet)()

    def __str__(self):
        return self.title
