from django.conf import settings
from django.db import models
from django.utils import timezone


class UserGuide(models.Model):
    name = models.CharField("Nom du Guide", max_length=200, unique=True)
    description = models.TextField("Description", blank=True)
    url = models.URLField(verbose_name="URL", max_length=250, unique=True, help_text="URL de la page à guider")
    guided_users = models.ManyToManyField(
        verbose_name="Utilisateurs guidés",
        to=settings.AUTH_USER_MODEL,
        help_text="Utilisateurs qui ont déjà été guidés",
        blank=True,
    )
    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Guide utilisateurs"
        verbose_name_plural = "Guides utilisateurs"

    def __str__(self):
        return self.name


class GuideStep(models.Model):
    class PositionChoices(models.TextChoices):
        TOP = "top", "Top"
        BOTTOM = "bottom", "Bottom"
        LEFT = "left", "Left"
        RIGHT = "right", "Right"

    guide = models.ForeignKey(UserGuide, related_name="steps", on_delete=models.CASCADE)
    title = models.CharField("Titre dans la popup", max_length=200)
    text = models.TextField("Contenu text de l'étape", blank=True)
    element = models.CharField("Élément css à rattacher", max_length=200)
    position = models.CharField(max_length=50, choices=PositionChoices.choices)

    class Meta:
        verbose_name = "Étape du guide"
        verbose_name_plural = "Étapes du guide"

    def __str__(self):
        return self.title
