from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.db.models import BooleanField, Case, Count, ExpressionWrapper, F, IntegerField, Q, Sum, When
from django.db.models.functions import Greatest
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django_better_admin_arrayfield.models.fields import ArrayField

from lemarche.perimeters.models import Perimeter
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.users.models import User
from lemarche.utils import constants
from lemarche.utils.fields import ChoiceArrayField


def get_perimeter_filter(siae):
    return (
        Q(perimeters__post_codes__contains=[siae.post_code])
        | Q(perimeters__insee_code=siae.department)
        | Q(perimeters__name=siae.region)
    )


class TenderQuerySet(models.QuerySet):
    def prefetch_many_to_many(self):
        return self.prefetch_related("sectors")  # "perimeters", "siaes"

    def select_foreign_keys(self):
        return self.select_related("location")

    def by_user(self, user):
        return self.filter(author=user)

    def validated(self):
        return self.filter(validated_at__isnull=False)

    def is_incremental(self):
        return self.filter(
            scale_marche_useless__in=[
                tender_constants.SURVEY_SCALE_QUESTION_0,
                tender_constants.SURVEY_SCALE_QUESTION_1,
            ]
        )

    def is_live(self):
        return self.validated().filter(deadline_date__gte=datetime.today())

    def in_perimeters(self, post_code, department, region):
        filters = (
            Q(perimeters__post_codes__contains=[post_code])
            | Q(perimeters__insee_code=department)
            | Q(perimeters__name=region)
        )
        # add distance?
        return self.filter(filters).distinct()

    def in_sectors(self, sectors):
        if sectors:
            return self.filter(sectors__in=sectors).distinct()
        else:
            return self

    def filter_with_siaes(self, siaes):
        """
        Return the list of tenders corresponding to the list of Siaes
        - the tender-siae matching has already been done with filter_with_tender()
        - we return only validated tenders
        """
        return self.filter(tendersiae__siae__in=siaes).validated().distinct()

    def with_deadline_date_is_outdated(self, limit_date=datetime.today()):
        return self.annotate(
            deadline_date_is_outdated=ExpressionWrapper(Q(deadline_date__lt=limit_date), output_field=BooleanField())
        )

    def order_by_deadline_date(self, limit_date=datetime.today()):
        return self.with_deadline_date_is_outdated(limit_date=limit_date).order_by(
            "deadline_date_is_outdated", "deadline_date", "-updated_at"
        )

    def with_siae_stats(self):
        """
        Enrich each Tender with stats on their linked Siae
        """
        return self.annotate(
            siae_count=Count("siaes", distinct=True),
            siae_email_send_count=Sum(
                Case(When(tendersiae__email_send_date__isnull=False, then=1), default=0, output_field=IntegerField())
            ),
            siae_email_link_click_count=Sum(
                Case(
                    When(tendersiae__email_link_click_date__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_display_count=Sum(
                Case(
                    When(tendersiae__detail_display_date__isnull=False, then=1), default=0, output_field=IntegerField()
                )
            ),
            siae_detail_contact_click_count=Sum(
                Case(
                    When(tendersiae__detail_contact_click_date__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_contact_click_since_last_seen_date_count=Sum(
                Case(
                    When(
                        tendersiae__detail_contact_click_date__gte=Greatest(
                            F("siae_list_last_seen_date"), F("created_at")
                        ),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )

    def with_network_siae_stats(self, network_siaes):
        return self.annotate(
            network_siae_email_send_count=Sum(
                Case(
                    When(Q(tendersiae__email_send_date__isnull=False) & Q(tendersiae__siae__in=network_siaes), then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            network_siae_detail_contact_click_count=Sum(
                Case(
                    When(
                        Q(tendersiae__detail_contact_click_date__isnull=False) & Q(tendersiae__siae__in=network_siaes),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )


class Tender(models.Model):
    """Appel d'offres et devis"""

    STATUS_DRAFT = tender_constants.STATUS_DRAFT
    STATUS_PUBLISHED = tender_constants.STATUS_PUBLISHED
    STATUS_VALIDATED = tender_constants.STATUS_VALIDATED

    TENDER_ACCEPT_SHARE_AMOUNT_TRUE = "✅ Montant partagé"
    TENDER_ACCEPT_SHARE_AMOUNT_FALSE = "❌ Montant non partagé"

    RESPONSE_KIND_EMAIL = "EMAIL"
    RESPONSE_KIND_TEL = "TEL"
    RESPONSE_KIND_EXTERNAL = "EXTERN"
    RESPONSE_KIND_CHOICES = (
        (RESPONSE_KIND_EMAIL, "E-mail"),
        (RESPONSE_KIND_TEL, "Téléphone"),
        (RESPONSE_KIND_EXTERNAL, "Lien externe"),
    )

    SOURCE_FORM = "FORM"
    SOURCE_FORM_CSRF = "FORM_CSRF"
    SOURCE_STAFF_C4_CREATED = "STAFF_C4_CREATED"
    SOURCE_API = "API"
    SOURCE_CHOICES = (
        (SOURCE_FORM, "Formulaire"),
        (SOURCE_FORM_CSRF, "Formulaire (erreur CSRF)"),
        (SOURCE_STAFF_C4_CREATED, "Staff Marché (via l'Admin)"),
        (SOURCE_API, "API"),
    )

    title = models.CharField(verbose_name="Titre du besoin", max_length=255)
    slug = models.SlugField(verbose_name="Slug", max_length=255, unique=True)
    kind = models.CharField(
        verbose_name="Type de besoin",
        max_length=6,
        choices=tender_constants.KIND_CHOICES,
        default=tender_constants.KIND_TENDER,
    )
    description = models.TextField(
        verbose_name="Description du besoin", help_text="Décrivez en quelques mots votre besoin", blank=True
    )
    presta_type = ChoiceArrayField(
        verbose_name="Type de prestation",
        base_field=models.CharField(max_length=20, choices=siae_constants.PRESTA_CHOICES),
        blank=True,
        default=list,
    )
    constraints = models.TextField(
        verbose_name="Contraintes techniques spécifiques",
        help_text="Renseignez les contraintes liées à votre besoin",
        blank=True,
    )
    external_link = models.URLField(
        verbose_name="Lien vers l'appel d'offres", help_text="Ajoutez ici l'URL de votre appel d'offres", blank=True
    )
    deadline_date = models.DateField(
        verbose_name="Date de clôture des réponses",
        help_text="Sélectionnez la date jusqu'à laquelle vous acceptez des réponses",
        blank=True,
        null=True,
    )
    start_working_date = models.DateField(verbose_name="Date idéale de début des prestations", blank=True, null=True)
    amount = models.CharField(
        verbose_name="Montant du besoin",
        help_text="Sélectionnez le montant reservé aux structures d'insertion et/ou de handicap",
        max_length=9,
        choices=tender_constants.AMOUNT_RANGE_CHOICES,
        blank=True,
        null=True,
    )
    why_amount_is_blank = models.CharField(
        verbose_name="Pourquoi le montant du besoin n'est pas renseigné ?",
        max_length=18,
        choices=tender_constants.WHY_AMOUNT_IS_BLANK_CHOICES,
        blank=True,
        null=True,
    )
    accept_share_amount = models.BooleanField(
        verbose_name="Partage du montant du besoin",
        help_text="Je souhaite partager ce montant aux prestataires inclusifs recevant mon besoin",
        default=False,
    )
    response_kind = ChoiceArrayField(
        verbose_name="Comment souhaitez-vous être contacté ?",
        base_field=models.CharField(max_length=6, choices=RESPONSE_KIND_CHOICES),
        blank=True,
        default=list,
    )
    accept_cocontracting = models.BooleanField(
        verbose_name="Ouvert à la co-traitance",
        help_text="Ce besoin peut être répondu par plusieurs prestataires (co-traitance ou sous-traitance)",
        default=False,
    )

    contact_first_name = models.CharField(verbose_name="Prénom du contact", max_length=255, blank=True)
    contact_last_name = models.CharField(verbose_name="Nom de famille du contact", max_length=255, blank=True)
    contact_email = models.EmailField(
        verbose_name="E-mail du contact", help_text="Renseignez votre adresse e-mail professionnelle", blank=True
    )
    contact_phone = models.CharField(
        verbose_name="Téléphone du contact",
        help_text="Renseignez votre numéro de téléphone professionnel",
        max_length=20,
        blank=True,
    )

    sectors = models.ManyToManyField(
        "sectors.Sector",
        verbose_name="Secteurs d'activité",
        related_name="tenders",
        blank=False,
        help_text="Sélectionnez un ou plusieurs secteurs d'activité",
    )
    location: Perimeter = models.ForeignKey(
        to="perimeters.Perimeter",
        verbose_name="Lieu d'intervention",
        related_name="tenders_location",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    perimeters = models.ManyToManyField(
        "perimeters.Perimeter",
        verbose_name="Périmètres ciblés",
        related_name="tenders",
        blank=True,
        help_text="Ajoutez un ou plusieurs lieux d'exécutions",
    )
    include_country_area = models.BooleanField(
        verbose_name="Inclure les structures qui ont comme périmètre d'intervention 'France entière' ?",
        help_text="Laisser vide pour exclure les structures qui ont comme périmètre d'intervention 'France entière'",
        default=False,
    )
    is_country_area = models.BooleanField(
        verbose_name="France entière",
        help_text="Retournera uniquement les structures qui ont comme périmètre d'intervention 'France entière'",
        default=False,
    )
    siae_kind = ChoiceArrayField(
        verbose_name="Type de structure",
        base_field=models.CharField(max_length=20, choices=siae_constants.KIND_CHOICES),
        blank=True,
        default=list,
    )

    author: User = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        verbose_name="Auteur",
        related_name="tenders",
        on_delete=models.CASCADE,
        blank=True,
    )

    siaes = models.ManyToManyField(
        "siaes.Siae",
        through="tenders.TenderSiae",
        verbose_name="Structures correspondantes au besoin",
        related_name="tenders",
        blank=True,
    )

    siae_transactioned = models.BooleanField(
        verbose_name="Abouti à une transaction avec une structure",
        default=False,
    )

    # validation
    status = models.CharField(
        verbose_name="Statut",
        max_length=10,
        choices=tender_constants.STATUS_CHOICES,
        default=tender_constants.STATUS_DRAFT,
    )
    validated_at = models.DateTimeField("Date de validation", blank=True, null=True)

    # survey
    scale_marche_useless = models.CharField(
        verbose_name="Utilité du marché de l'inclusion",
        help_text="Q°1. Si le Marché de l'inclusion n'existait pas, auriez-vous consulté des prestataires inclusifs* pour ce besoin ?",  # noqa
        max_length=2,
        choices=tender_constants.SURVEY_SCALE_QUESTION_CHOICES,
        default=tender_constants.SURVEY_SCALE_QUESTION_0,
    )

    marche_benefits = ChoiceArrayField(
        verbose_name="Bénéfices du marché de l'inclusion",
        help_text="Pour ce besoin, quels sont les bénéfices de passer par le Marché de l'inclusion ?",
        base_field=models.CharField(max_length=20, choices=constants.MARCHE_BENEFIT_CHOICES),
        blank=True,
        default=list,
    )

    # stats
    siae_list_last_seen_date = models.DateTimeField(
        "Date de dernière visite de l'auteur sur la page 'structures intéressées'", blank=True, null=True
    )
    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)
    source = models.CharField(verbose_name="Source", max_length=20, choices=SOURCE_CHOICES, default=SOURCE_FORM)
    extra_data = models.JSONField(verbose_name="Données complémentaires", editable=False, default=dict)
    import_raw_object = models.JSONField(verbose_name="Données d'import", editable=False, null=True)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(TenderQuerySet)()

    class Meta:
        verbose_name = "Besoin d'acheteur"
        verbose_name_plural = "Besoins des acheteurs"
        ordering = ["-created_at", "deadline_date"]

    def __str__(self):
        return self.title

    def set_slug(self, with_uuid=False):
        """
        The slug field should be unique.
        """
        if not self.slug:
            self.slug = slugify(f"{self.title}-{str(self.author.company_name or '')}")[:40]
        if with_uuid:
            self.slug += f"-{str(uuid4())[:4]}"

    def set_siae_found_list(self):
        """
        Where the Tender-Siae matching magic happens!
        Called by Tender signals (and if not self.validated_at)
        """
        siae_found_list = Siae.objects.filter_with_tender(self)
        self.siaes.set(siae_found_list)

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
    def contact_full_name(self):
        return f"{self.contact_first_name} {self.contact_last_name}"

    def sectors_list_string(self, display_max=5):
        sectors_name_list = self.sectors.form_filter_queryset().values_list("name", flat=True)
        if display_max and len(sectors_name_list) > display_max:
            sectors_name_list = sectors_name_list[:display_max]
            sectors_name_list.append("…")
        return ", ".join(sectors_name_list)

    def sectors_full_list_string(self):
        return self.sectors_list_string(display_max=None)

    @cached_property
    def perimeters_list_string(self):
        return ", ".join(self.perimeters.values_list("name", flat=True))

    @cached_property
    def location_display(self):
        if self.is_country_area:
            return "France entière"
        elif self.location:
            return self.location.name_display
        else:
            # maintain legacy perimeters display
            return self.perimeters_list_string

    @cached_property
    def external_link_title(self):
        if self.kind == tender_constants.KIND_TENDER:
            return "Voir l'appel d'offres"
        return "Lien partagé"

    @property
    def cta_text(self):
        if self.kind == tender_constants.KIND_TENDER:
            return "Voir cet appel d'offres"
        return "Répondre à cette opportunité"

    @cached_property
    def can_display_contact_email(self):
        return (self.RESPONSE_KIND_EMAIL in self.response_kind) and self.contact_email

    @cached_property
    def can_display_contact_phone(self):
        return (self.RESPONSE_KIND_TEL in self.response_kind) and self.contact_phone

    @cached_property
    def can_display_contact_external_link(self):
        return (self.RESPONSE_KIND_EXTERNAL in self.response_kind) and self.external_link

    @cached_property
    def response_kind_is_only_external(self):
        return (len(self.response_kind) == 1) and self.can_display_contact_external_link

    @cached_property
    def accept_share_amount_display(self):
        if self.accept_share_amount:
            return self.TENDER_ACCEPT_SHARE_AMOUNT_TRUE
        return self.TENDER_ACCEPT_SHARE_AMOUNT_FALSE

    @cached_property
    def deadline_date_outdated(self):
        if self.deadline_date and self.deadline_date < timezone.now().date():
            return True
        return False

    @property
    def hubspot_deal_id(self):
        return self.extra_data.get("hubspot_deal_id")

    @property
    def siae_detail_display_date_count(self):
        return self.tendersiae_set.filter(detail_display_date__isnull=False).count()

    @property
    def siae_detail_display_date_count_all(self):
        """
        Return all siae that have seen the tender (via e-mail or link or both)
        """
        return (
            self.tendersiae_set.filter(Q(email_link_click_date__isnull=False) | Q(detail_display_date__isnull=False))
            .distinct()
            .count()
        )

    @property
    def siae_email_send_date_count(self):
        return self.tendersiae_set.filter(email_send_date__isnull=False).count()

    @property
    def siae_detail_contact_click_date_count(self):
        return self.tendersiae_set.filter(detail_contact_click_date__isnull=False).count()

    def get_absolute_url(self):
        return reverse("tenders:detail", kwargs={"slug": self.slug})

    def set_hubspot_id(self, hubspot_deal_id, with_save=True):
        self.extra_data.update({"hubspot_deal_id": hubspot_deal_id})
        if with_save:
            self.save()

    def set_validated(self, with_save=True):
        self.validated_at = datetime.now()
        self.status = tender_constants.STATUS_VALIDATED
        log_item = {
            "action": "validate",
            "date": str(self.validated_at),
        }
        self.logs.append(log_item)
        if with_save:
            self.save()


@receiver(post_save, sender=Tender)
def tender_post_save(sender, instance=Tender, **kwargs):
    if not instance.validated_at and instance.status == tender_constants.STATUS_PUBLISHED:
        instance.set_siae_found_list()


@receiver(m2m_changed, sender=Tender.sectors.through)
@receiver(m2m_changed, sender=Tender.perimeters.through)
def tender_m2m_changed(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        if not instance.validated_at and instance.status == tender_constants.STATUS_PUBLISHED:
            instance.set_siae_found_list()


class TenderSiae(models.Model):
    TENDER_SIAE_SOURCE_EMAIL = "EMAIL"
    TENDER_SIAE_SOURCE_DASHBOARD = "DASHBOARD"
    TENDER_SIAE_SOURCE_LINK = "LINK"
    TENDER_SIAE_SOURCE_CHOICES = (
        (TENDER_SIAE_SOURCE_EMAIL, "E-mail"),
        (TENDER_SIAE_SOURCE_DASHBOARD, "Dashboard"),
        (TENDER_SIAE_SOURCE_LINK, "Lien"),
    )

    tender = models.ForeignKey("tenders.Tender", verbose_name="Besoin d'acheteur", on_delete=models.CASCADE)
    siae = models.ForeignKey("siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE)

    source = models.CharField(max_length=20, choices=TENDER_SIAE_SOURCE_CHOICES, default=TENDER_SIAE_SOURCE_EMAIL)

    # stats
    email_send_date = models.DateTimeField("Date d'envoi de l'e-mail", blank=True, null=True)
    email_link_click_date = models.DateTimeField("Date de clic sur le lien dans l'e-mail", blank=True, null=True)
    detail_display_date = models.DateTimeField("Date de visualisation du besoin", blank=True, null=True)
    detail_contact_click_date = models.DateTimeField(
        "Date de clic sur les coordonnées du besoin", blank=True, null=True
    )
    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Structure correspondant au besoin"
        verbose_name_plural = "Structures correspondantes au besoin"
        ordering = ["-created_at"]


class PartnerShareTenderQuerySet(models.QuerySet):
    def filter_by_amount(self, tender: Tender):
        """
        Return partners with:
        - an empty 'amount_in'
        - or an 'amount_in' at least equal or greater than the tenders' 'amount'
        """
        conditions = Q()
        if tender.amount:
            conditions |= Q(amount_in__isnull=True)
            try:
                amount_index = tender_constants.AMOUNT_RANGE_LIST.index(tender.amount)
                conditions |= Q(amount_in__in=tender_constants.AMOUNT_RANGE_LIST[amount_index:])
            except ValueError:
                pass
        return self.filter(conditions)

    def filter_by_perimeter(self, tender: Tender):
        """
        Return partners with:
        - an empty 'perimeters'
        - or with 'perimeters' that overlaps with the tenders' 'perimeters'
        (we suppose that tenders always have 'is_country_area' or 'perimeters' filled)
        """
        conditions = Q(perimeters__isnull=True)
        if not tender.is_country_area:
            # conditions = Q(perimeters__in=tender.perimeters.all()) | Q(perimeters__isnull=True)
            for perimeter in tender.perimeters.all():
                if perimeter.kind == Perimeter.KIND_CITY:
                    conditions |= Q(perimeters__in=[perimeter])
                    conditions |= Q(perimeters__insee_code=perimeter.department_code)
                    conditions |= Q(perimeters__insee_code=f"R{perimeter.region_code}")
                elif perimeter.kind == Perimeter.KIND_DEPARTMENT:
                    conditions |= Q(perimeters__in=[perimeter])
                    conditions |= Q(perimeters__insee_code=f"R{perimeter.region_code}")
                elif perimeter.kind == Perimeter.KIND_REGION:
                    conditions |= Q(perimeters__in=[perimeter])
        return self.filter(conditions)

    def filter_by_tender(self, tender: Tender):
        return self.filter_by_amount(tender).filter_by_perimeter(tender).distinct()
        # return self.filter_by_amount(tender).distinct()


class PartnerShareTender(models.Model):
    name = models.CharField(max_length=120, verbose_name="Nom du partenaire")

    perimeters = models.ManyToManyField(
        "perimeters.Perimeter", verbose_name="Lieux de filtrage", related_name="partner_share_tenders", blank=True
    )
    amount_in = models.CharField(
        verbose_name="Montant du marché limite",
        max_length=9,
        choices=tender_constants.AMOUNT_RANGE_CHOICES,
        blank=True,
        null=True,
    )

    contact_email_list = ArrayField(
        verbose_name="Liste de contact", base_field=models.EmailField(max_length=255), blank=True, default=list
    )

    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(PartnerShareTenderQuerySet)()

    class Meta:
        verbose_name = "Partenaire intéressé des dépôts de besoins"
        verbose_name_plural = "Partenaires intéressés des dépôts de besoins"

    @cached_property
    def perimeters_list_string(self) -> str:
        return ", ".join(self.perimeters.values_list("name", flat=True))
