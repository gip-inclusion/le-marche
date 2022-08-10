from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class CodeQuerySet(models.QuerySet):
    def has_sector(self):
        """Only return codes who have at least 1 Sector."""
        return self.prefetch_related("sectors").filter(sectors__isnull=False).distinct()


class Code(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    cpv_code = models.CharField(verbose_name="Code", max_length=8)
    hierarchy_level = models.IntegerField(
        verbose_name="Niveau hiérarchique", validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activité", related_name="cpv_codes", blank=True
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(CodeQuerySet)()

    class Meta:
        verbose_name = "Code CPV"
        verbose_name_plural = "Code CPV"
        ordering = ["cpv_code"]

    def __str__(self):
        return f"{self.name} ({self.cpv_code})"

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = f"{str(self.cpv_code)}-{slugify(self.name)[:40]}"

    def set_hierarchy_level(self):
        """
        From 1 (XX000000) to 7 (XXXXXXXX).
        """
        if self.cpv_code:
            cpv_code_small = self.cpv_code[2:]
            self.hierarchy_level = len(cpv_code_small.rstrip("0")) + 1

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        self.set_hierarchy_level()
        super().save(*args, **kwargs)
