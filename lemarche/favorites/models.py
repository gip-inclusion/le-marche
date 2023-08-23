from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone


class FavoriteListQuerySet(models.QuerySet):
    def by_user(self, user):
        return self.filter(user=user)


class FavoriteList(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur", related_name="favorite_lists", on_delete=models.CASCADE
    )
    siaes = models.ManyToManyField(
        "siaes.Siae",
        through="favorites.FavoriteItem",
        verbose_name="Structures en favoris",
        related_name="favorite_lists",
        blank=True,
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(FavoriteListQuerySet)()

    class Meta:
        verbose_name = "Liste de favoris"
        verbose_name_plural = "Listes de favoris"

    def __str__(self):
        return self.name

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = f"{slugify(self.name)[:40]}-{str(uuid4())[:4]}"

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)


@receiver(post_save, sender=FavoriteList)
@receiver(post_delete, sender=FavoriteList)
def favorite_list_changed(sender, instance, **kwargs):
    """
    Will be called when we create, update or delete a Favorite List
    """
    instance.user.favorite_list_count = instance.user.favorite_lists.count()
    instance.user.save()


class FavoriteItem(models.Model):
    siae = models.ForeignKey("siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE)
    favorite_list = models.ForeignKey(
        "favorites.FavoriteList", verbose_name="Liste de favoris", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Structure en favoris"
        verbose_name_plural = "Structures en favoris"
        ordering = ["-created_at"]
