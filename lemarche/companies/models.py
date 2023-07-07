from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django_better_admin_arrayfield.models.fields import ArrayField


class CompanyQuerySet(models.QuerySet):
    def has_user(self):
        return self.filter(users__isnull=False).distinct()

    def has_email_domain(self):
        return self.exclude(email_domain_list=[])


class Company(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    description = models.TextField(verbose_name="Description", blank=True)
    siret = models.CharField(verbose_name="Siret", max_length=14, blank=True)
    website = models.URLField(verbose_name="Site web", blank=True)
    logo_url = models.URLField(verbose_name="Lien vers le logo", max_length=500, blank=True)

    email_domain_list = ArrayField(
        verbose_name="Liste des noms de domaine d'e-mails",
        help_text="@entreprise.fr (sans le @)",
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(CompanyQuerySet)()

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

    def __str__(self):
        return self.name

    def set_slug(self):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = slugify(self.name)[:50]

    def save(self, *args, **kwargs):
        """Generate the slug field before saving."""
        self.set_slug()
        super().save(*args, **kwargs)
