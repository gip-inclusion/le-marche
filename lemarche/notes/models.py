from django.db import models
from django.utils import timezone


class Note(models.Model):
    text = models.TextField(verbose_name="Contenu de la note", blank=False)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
