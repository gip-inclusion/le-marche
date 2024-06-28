from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class UserGuide(models.Model):
    name = models.CharField("Nom du Guide", max_length=200, unique=True)
    description = models.TextField("Description", blank=True, null=True)
    slug = models.SlugField(
        "Slug (unique)",
        max_length=50,
        unique=True,
        help_text="Identifiant permettant d'identifier le guide en js",
        null=True,
    )
    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

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
    guide = models.ForeignKey(UserGuide, related_name="steps", on_delete=models.CASCADE)
    title = models.CharField("Titre dans la popup", max_length=200)
    text = models.TextField("Contenu text de l'étape")
    element = models.CharField("Élément css à rattacher", max_length=200, null=True)
    position = models.CharField(
        max_length=50, choices=[("top", "Top"), ("bottom", "Bottom"), ("left", "Left"), ("right", "Right")], null=True
    )

    def __str__(self):
        return self.title
