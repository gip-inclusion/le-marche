import datetime
from functools import reduce
from uuid import uuid4

import _operator
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify


class TenderQuerySet(models.QuerySet):
    def by_user(self, user):
        return self.filter(author=user)

    def find_in_perimeters(self, post_code, department, region):
        filters = (
            Q(perimeters__post_codes__contains=[post_code])
            | Q(perimeters__insee_code=department)
            | Q(perimeters__name=region)
        )
        # add distance?
        return self.filter(filters).distinct()

    def in_sectors(self, sectors):
        if sectors:
            query = reduce(_operator.or_, (Q(sectors__id__contains=item.id) for item in sectors))
            return self.filter(query).distinct()
        else:
            return self

    def filter_with_siae(self, siae):
        """
        Return the list of tenders corresponding to the Siae
        Filters on its sectors & perimeter
        """
        sectors = siae.sectors.all()
        qs = self.prefetch_related("sectors", "perimeters").in_sectors(sectors)
        if siae.geo_range != siae.GEO_RANGE_COUNTRY:
            qs.find_in_perimeters(post_code=siae.post_code, department=siae.department, region=siae.region)
        return qs.distinct()


class Tender(models.Model):
    """Appel d'offre et devis"""

    TENDER_KIND_TENDER = "TENDER"
    TENDER_KIND_QUOTE = "QUOTE"
    TENDER_KIND_BOAMP = "BOAMP"
    TENDER_KIND_PROJECT = "PROJ"

    TENDER_KIND_CHOICES = (
        (TENDER_KIND_TENDER, "Appel d'offre"),
        (TENDER_KIND_QUOTE, "Devis"),
        (TENDER_KIND_PROJECT, "Projet d'achat"),
    )

    RESPONSE_KIND_EMAIL = "EMAIL"
    RESPONSE_KIND_TEL = "TEL"
    RESPONSE_KIND_EXTERNAL = "EXTERN"

    RESPONSE_KIND_CHOICES = (
        (RESPONSE_KIND_EMAIL, "E-mail"),
        (RESPONSE_KIND_TEL, "Téléphone"),
        (RESPONSE_KIND_EXTERNAL, "Lien externe"),
    )

    title = models.CharField(verbose_name="Titre du besoin", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    kind = models.CharField(
        verbose_name="Type de besoin", max_length=6, choices=TENDER_KIND_CHOICES, default=TENDER_KIND_TENDER
    )
    description = models.TextField(verbose_name="Description du besoin", blank=True)
    constraints = models.TextField(verbose_name="Contraintes techniques spécifiques", blank=True)
    external_link = models.URLField(verbose_name="Lien vers l'appel d'offre", blank=True)
    deadline_date = models.DateField(verbose_name="Date de clôture des réponses")
    start_working_date = models.DateField(verbose_name="Date idéale de début des prestations", blank=True, null=True)
    amount = models.PositiveIntegerField(verbose_name="Montant du marché", blank=True, null=True)
    response_kind = ArrayField(
        models.CharField(max_length=6, choices=RESPONSE_KIND_CHOICES),
        verbose_name="Comment souhaitez-vous être contacté ?",
    )

    contact_first_name = models.CharField(verbose_name="Prénom du contact", max_length=255, blank=True)
    contact_last_name = models.CharField(verbose_name="Nom de famille du contact", max_length=255, blank=True)
    contact_email = models.EmailField(verbose_name="E-mail du contact", blank=True)
    contact_phone = models.CharField(verbose_name="Téléphone du contact", max_length=20, blank=True)

    perimeters = models.ManyToManyField(
        "perimeters.Perimeter", verbose_name="Lieux d'exécution", related_name="tenders", blank=False
    )
    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activité", related_name="tenders", blank=False
    )

    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, related_name="tenders", on_delete=models.CASCADE, blank=True
    )

    siae_found_count = models.PositiveIntegerField(verbose_name="Nombre de SIAE trouvées", default=0)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(TenderQuerySet)()

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
    def get_contact_full_name(self):
        return f"{self.contact_first_name} {self.contact_last_name}"

    @cached_property
    def get_sectors_names(self):
        return ", ".join(self.sectors.values_list("name", flat=True))

    @cached_property
    def get_perimeters_names(self):
        return ", ".join(self.perimeters.values_list("name", flat=True))

    def get_absolute_url(self):
        return reverse("tenders:detail", kwargs={"slug": self.slug})
