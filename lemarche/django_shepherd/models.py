from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class UserGuide(models.Model):
    name = models.CharField("Nom du Guide", max_length=200, unique=True)
    description = models.TextField("Description", blank=True)
    slug = models.SlugField(
        "Slug (unique)",
        max_length=50,
        unique=True,
        help_text="Identifiant permettant d'identifier le guide en js",
    )
    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Guide utilisateurs"
        verbose_name_plural = "Guides utilisateurs"

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = slugify(self.name)[:50]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)


class GuideStep(models.Model):
    class PositionChoices(models.TextChoices):
        TOP = "TOP", "Top"
        BOTTOM = "BOTTOM", "Bottom"
        LEFT = "LEFT", "Left"
        RIGHT = "RIGHT", "Right"

    guide = models.ForeignKey(UserGuide, related_name="steps", on_delete=models.CASCADE)
    title = models.CharField("Titre dans la popup", max_length=200)
    text = models.TextField("Contenu text de l'étape")
    element = models.CharField("Élément css à rattacher", max_length=200)
    position = models.CharField(max_length=50, choices=PositionChoices.choices)

    class Meta:
        verbose_name = "Étape du guide"
        verbose_name_plural = "Étapes du guide"

    def __str__(self):
        return self.title
