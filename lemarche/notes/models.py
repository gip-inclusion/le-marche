from django.conf import settings
from django.db import models
from django.utils import timezone

from lemarche.users.models import User


class Note(models.Model):
    text = models.TextField(verbose_name="Contenu de la note", blank=False)

    author: User = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        verbose_name="Auteur",
        related_name="notes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
