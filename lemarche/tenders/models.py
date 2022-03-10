import datetime
from functools import reduce
from uuid import uuid4

import _operator
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.db.models.manager import BaseManager
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify


class TenderQuerySet(models.QuerySet):
    def created_by_user(self, user):
        return self.filter(author=user)

    def find_in_perimeters(self, post_code, coords, department, region):
        filters = (
            Q(perimeters__post_codes__contains=[post_code])
            | Q(perimeters__insee_code=department)
            | Q(perimeters__name=region)
        )
        # add distance
        queryset = self.filter(filters).distinct()
        return queryset

    def in_sectors(self, sectors):
        query = reduce(_operator.or_, (Q(sectors__id__contains=item.id) for item in sectors))
        return self.filter(query).distinct()


class TenderManager(BaseManager.from_queryset(TenderQuerySet)):
    pass


class Tender(models.Model):
    """Appel d'offre et devis"""

    TENDERS_KIND_TENDER = "TENDER"
    TENDERS_KIND_QUOTE = "QUOTE"
    TENDERS_KIND_BOAMP = "BOAMP"

    TENDERS_KIND_CHOICES = (
        (TENDERS_KIND_TENDER, "Appel d'offre"),
        (TENDERS_KIND_QUOTE, "Devis"),
    )

    RESPONSES_KIND_EMAIL = "EMAIL"
    RESPONSES_KIND_TEL = "TEL"
    RESPONSES_KIND_EXTERNAL = "EXTERN"

    RESPONSES_KIND_CHOICES = (
        (RESPONSES_KIND_EMAIL, "Email"),
        (RESPONSES_KIND_TEL, "Téléphone"),
        (RESPONSES_KIND_EXTERNAL, "Lien externe"),
    )

    kind = models.CharField(
        verbose_name="Type de besoin", max_length=6, choices=TENDERS_KIND_CHOICES, default=TENDERS_KIND_TENDER
    )

    title = models.CharField(verbose_name="Titre du besoin", max_length=255)
    description = models.TextField(verbose_name="Description du besoin", blank=True)
    constraints = models.TextField(verbose_name="Contraintes techniques spécifiques", blank=True)
    external_link = models.URLField(verbose_name="Lien vers l’appel d’offre", blank=True)
    deadline_date = models.DateField(verbose_name="Date de clôture des réponses")
    start_working_date = models.DateField(verbose_name="Date idéale de début des prestations", blank=True, null=True)
    contact_first_name = models.CharField(verbose_name="Prénom du contact", max_length=255, blank=True)
    contact_last_name = models.CharField(verbose_name="Nom de famille du contact", max_length=255, blank=True)
    contact_email = models.EmailField(verbose_name="Email du contact", blank=True)
    contact_phone = models.CharField(verbose_name="Téléphone du contact", max_length=20, blank=True)
    amount = models.PositiveIntegerField(verbose_name="Montant du marché", blank=True, null=True)
    response_kind = ArrayField(
        models.CharField(max_length=6, choices=RESPONSES_KIND_CHOICES),
        verbose_name="Comment souhaitez-vous être contacté ?",
    )

    perimeters = models.ManyToManyField(
        "perimeters.Perimeter", verbose_name="Lieux d'exécutions", related_name="tenders", blank=False
    )
    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activités", related_name="tenders", blank=False
    )

    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, related_name="tenders", on_delete=models.CASCADE, blank=True
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)

    objects = TenderManager()

    class Meta:
        verbose_name = "Besoin d'acheteur"
        verbose_name_plural = "Besoins des acheteurs"
        ordering = ["-updated_at", "deadline_date"]

    def clean(self):
        today = datetime.date.today()
        if self.deadline_date < today:
            raise ValidationError("La date de cloture des réponses ne doit pas être antérieure à aujourd'hui.")

        if self.start_working_date and self.start_working_date < self.deadline_date:
            raise ValidationError(
                "La date idéale de début des prestations ne doit pas être antérieure de cloture des réponses."
            )

    def __str__(self):
        return self.title

    def set_slug(self, with_uuid=False):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = f"{slugify(self.title)[:40]}-{str(self.author.company_name or '')}"
        if with_uuid:
            self.slug += f"-{str(uuid4())[:4]}"

    def save(self, *args, **kwargs):
        """
        - update the object stats
        - update the object content_fill_dates
        - generate the slug field
        """
        try:
            self.set_slug()
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError as e:
            # check that it's a slug conflict
            # Full message expected: duplicate key value violates unique constraint "tenders_tender_slug_0f0b821f_uniq" DETAIL:  Key (slug)=(...) already exists.  # noqa
            if "tenders_tender_slug" in str(e):
                self.set_slug(with_uuid=True)
                super().save(*args, **kwargs)
            else:
                raise e

    @cached_property
    def contact_infos(self):
        return {
            "full_name": f"{self.contact_first_name} {self.contact_last_name}",
            "company": self.author.company_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
        }

    @cached_property
    def get_kind_name(self):
        for key, value in self.TENDERS_KIND_CHOICES:
            if self.kind == key:
                return value

    @cached_property
    def get_sectors_names(self):
        return ", ".join(self.sectors.values_list("name", flat=True))

    @cached_property
    def get_perimeters_names(self):
        return ", ".join(self.perimeters.values_list("name", flat=True))

    def get_absolute_url(self):
        return reverse("tenders:add", kwargs={"pk": self.pk})
