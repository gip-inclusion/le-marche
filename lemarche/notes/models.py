from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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

    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
