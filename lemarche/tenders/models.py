from datetime import datetime, timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import IntegrityError, models, transaction
from django.db.models import BooleanField, Case, Count, ExpressionWrapper, F, IntegerField, Q, Sum, When
from django.db.models.functions import Greatest
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django_better_admin_arrayfield.models.fields import ArrayField
from django_extensions.db.fields import ShortUUIDField
from shortuuid import uuid

from lemarche.perimeters.models import Perimeter
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.users.models import User
from lemarche.utils.constants import MARCHE_BENEFIT_CHOICES, RECALCULATED_FIELD_HELP_TEXT
from lemarche.utils.fields import ChoiceArrayField


def get_perimeter_filter(siae):
    return (
        Q(perimeters__post_codes__contains=[siae.post_code])
        | Q(perimeters__insee_code=siae.department)
        | Q(perimeters__name=siae.region)
    )


class TenderQuerySet(models.QuerySet):
    def prefetch_many_to_many(self):
        return self.prefetch_related("sectors")  # "perimeters", "siaes", "questions"

    def select_foreign_keys(self):
        return self.select_related("location")

    def by_user(self, user):
        return self.filter(author=user)

    def validated(self):
        return self.filter(validated_at__isnull=False)

    def validated_but_not_sent(self):
        yesterday = timezone.now() - timedelta(days=1)

        return self.with_siae_stats().filter(
            (Q(version=0) & Q(validated_at__isnull=False) & Q(first_sent_at__isnull=True))
            | (
                Q(version=1)
                & Q(validated_at__isnull=False)
                & Q(siae_detail_contact_click_count_annotated__lte=F("limit_nb_siae_interested"))
                & ~Q(siae_count_annotated=F("siae_email_send_count_annotated"))
                & (Q(first_sent_at__isnull=True) | Q(last_sent_at__lt=yesterday))
            )
        )

    def sent(self):
        return self.filter(first_sent_at__isnull=False)

    def is_incremental(self):
        return self.filter(
            scale_marche_useless__in=[
                tender_constants.SURVEY_SCALE_QUESTION_0,
                tender_constants.SURVEY_SCALE_QUESTION_1,
            ]
        )

    def is_live(self):
        return self.sent().filter(deadline_date__gte=datetime.today())

    def has_amount(self):
        return self.filter(Q(amount__isnull=False) | Q(amount_exact__isnull=False))

    def transaction_survey_email(self, kind=None, all=False):
        seven_days_ago = datetime.today().date() - timedelta(days=7)
        qs = self.sent().filter(survey_transactioned_answer=None)
        if kind:
            qs = qs.filter(kind=kind)
        if all:
            qs = qs.filter(deadline_date__lte=seven_days_ago)
        else:
            qs = qs.filter(deadline_date=seven_days_ago)
        return qs

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
        Return the list of tenders corresponding to the list of
        - we return only sent tenders
        - the tender-siae matching has already been done with filter_with_tender()
        """
        return self.sent().filter(tendersiae__siae__in=siaes).distinct()

    def with_deadline_date_is_outdated(self, limit_date=datetime.today()):
        return self.annotate(
            deadline_date_is_outdated_annotated=ExpressionWrapper(
                Q(deadline_date__lt=limit_date), output_field=BooleanField()
            )
        )

    def order_by_deadline_date(self, limit_date=datetime.today()):
        return self.with_deadline_date_is_outdated(limit_date=limit_date).order_by(
            "deadline_date_is_outdated_annotated", "deadline_date", "-updated_at"
        )

    def with_question_stats(self):
        return self.annotate(question_count_annotated=Count("questions", distinct=True))

    def with_siae_stats(self):
        """
        Enrich each Tender with stats on their linked Siae
        """
        return self.annotate(
            siae_count_annotated=Count("siaes", distinct=True),
            siae_email_send_count_annotated=Sum(
                Case(When(tendersiae__email_send_date__isnull=False, then=1), default=0, output_field=IntegerField())
            ),
            siae_email_link_click_count_annotated=Sum(
                Case(
                    When(tendersiae__email_link_click_date__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_display_count_annotated=Sum(
                Case(
                    When(tendersiae__detail_display_date__isnull=False, then=1), default=0, output_field=IntegerField()
                )
            ),
            siae_email_link_click_or_detail_display_count_annotated=Sum(
                Case(
                    When(
                        Q(tendersiae__email_link_click_date__isnull=False)
                        | Q(tendersiae__detail_display_date__isnull=False),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_contact_click_count_annotated=Sum(
                Case(
                    When(tendersiae__detail_contact_click_date__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_cocontracting_click_count_annotated=Sum(
                Case(
                    When(tendersiae__detail_cocontracting_click_date__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_not_interested_click_count_annotated=Sum(
                Case(
                    When(tendersiae__detail_not_interested_click_date__isnull=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            siae_detail_contact_click_since_last_seen_date_count_annotated=Sum(
                Case(
                    When(
                        tendersiae__detail_contact_click_date__gte=Greatest(
                            F("siae_list_last_seen_date"), F("created_at")
                        ),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                ),
            ),
        )

    def with_network_siae_stats(self, network_siaes):
        return self.annotate(
            network_siae_email_send_count_annotated=Sum(
                Case(
                    When(Q(tendersiae__email_send_date__isnull=False) & Q(tendersiae__siae__in=network_siaes), then=1),
                    default=0,
                    output_field=IntegerField(),
                ),
            ),
            network_siae_detail_contact_click_count_annotated=Sum(
                Case(
                    When(
                        Q(tendersiae__detail_contact_click_date__isnull=False) & Q(tendersiae__siae__in=network_siaes),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                ),
            ),
        )


class Tender(models.Model):
    """Appel d'offres, demande de devis et sourcing"""

    FIELDS_SURVEY_TRANSACTIONED = [
        "survey_transactioned_send_date",
        "survey_transactioned_answer",
        "survey_transactioned_amount",
        "survey_transactioned_feedback",
        "survey_transactioned_answer_date",
    ]
    FIELDS_STATS_COUNT = [
        "siae_count",
        "siae_email_send_count",
        "siae_email_link_click_count",
        "siae_detail_display_count",
        "siae_email_link_click_or_detail_display_count",
        "siae_detail_contact_click_count",
        "siae_detail_cocontracting_click_count",
        "siae_detail_not_interested_click_count",
    ]
    FIELDS_STATS_TIMESTAMPS = [
        "published_at",
        "validated_at",
        "first_sent_at",
        "siae_list_last_seen_date",
        "created_at",
        "updated_at",
    ]
    FIELDS_STATS = FIELDS_STATS_COUNT + FIELDS_STATS_TIMESTAMPS + []
    READONLY_FIELDS = FIELDS_SURVEY_TRANSACTIONED + FIELDS_STATS

    # used in templates
    STATUS_DRAFT = tender_constants.STATUS_DRAFT
    STATUS_PUBLISHED = tender_constants.STATUS_PUBLISHED
    STATUS_VALIDATED = tender_constants.STATUS_VALIDATED

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
        base_field=models.CharField(max_length=6, choices=tender_constants.RESPONSE_KIND_CHOICES),
        blank=True,
        default=list,
    )

    response_is_anonymous = models.BooleanField(verbose_name="Je souhaite rester anonyme", blank=False, default=False)
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
    contact_company_name = models.CharField(
        verbose_name="Nom de l'entreprise du contact",
        help_text="Laisser vide pour afficher le nom de l'entreprise de l'auteur",
        max_length=255,
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
    distance_location = models.IntegerField(
        verbose_name="Distance en kilomètres autour du lieu d'intervention",
        blank=True,
        null=True,
        help_text=(
            "Si vous décidez de faire un ciblage en km, vérifiez que le lieu d’intervention est bien renseigné et est "
            "une ville et que le kilométrage indiqué correspond à la réalité du besoin et des prestataires en face"
        ),
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

    # survey
    scale_marche_useless = models.CharField(
        verbose_name="Utilité du marché de l'inclusion",
        help_text="Si le Marché de l'inclusion n'existait pas, auriez-vous consulté des prestataires inclusifs* pour ce besoin ?",  # noqa
        max_length=2,
        choices=tender_constants.SURVEY_SCALE_QUESTION_CHOICES,
        default=tender_constants.SURVEY_SCALE_QUESTION_0,
    )

    marche_benefits = ChoiceArrayField(
        verbose_name="Bénéfices du marché de l'inclusion",
        help_text="Pour ce besoin, quels sont les bénéfices de passer par le Marché de l'inclusion ?",
        base_field=models.CharField(max_length=20, choices=MARCHE_BENEFIT_CHOICES),
        blank=True,
        default=list,
    )
    survey_transactioned_send_date = models.DateTimeField(
        verbose_name="Sondage transaction : date d'envoi de l'e-mail", blank=True, null=True
    )
    survey_transactioned_answer = models.BooleanField(
        verbose_name="Sondage transaction : réponse", blank=True, null=True
    )
    survey_transactioned_amount = models.PositiveIntegerField(
        verbose_name="Sondage transaction : montant du besoin", blank=True, null=True
    )
    survey_transactioned_feedback = models.TextField(
        verbose_name="Sondage transaction : retour d'expérience", blank=True
    )
    survey_transactioned_answer_date = models.DateTimeField(
        "Sondage transaction : date de réponse", blank=True, null=True
    )

    # validation & send
    status = models.CharField(
        verbose_name="Statut",
        max_length=10,
        choices=tender_constants.STATUS_CHOICES,
        default=tender_constants.STATUS_DRAFT,
    )
    validated_at = models.DateTimeField("Date de validation", blank=True, null=True)
    first_sent_at = models.DateTimeField("Date du premier envoi", blank=True, null=True)
    last_sent_at = models.DateTimeField("Date du dernier envoi", blank=True, null=True)
    # admin
    notes = GenericRelation("notes.Note", related_query_name="tender")
    siae_transactioned = models.BooleanField(
        verbose_name="Abouti à une transaction avec une structure",
        help_text="Champ renseigné par un ADMIN",
        blank=True,
        null=True,
    )
    amount_exact = models.PositiveIntegerField(
        verbose_name="Montant exact du besoin", help_text="Champ renseigné par un ADMIN", blank=True, null=True
    )
    incremental_custom = models.PositiveSmallIntegerField(
        verbose_name="Modification de l'incrémental (%)",
        help_text="Champ renseigné par un ADMIN",
        blank=True,
        null=True,
        default=None,
    )
    limit_send_to_siae_batch = models.PositiveSmallIntegerField(
        verbose_name="Nombre de SIAES par envoi",
        help_text="Champ renseigné par un ADMIN",
        default=10,
    )

    limit_nb_siae_interested = models.PositiveSmallIntegerField(
        verbose_name="Limite des SIAES intéressées",
        help_text="Champ renseigné par un ADMIN",
        default=5,
    )
    # stats
    siae_count = models.IntegerField(
        "Nombre de structures concernées", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_email_send_count = models.IntegerField(
        "Nombre de structures contactées", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_email_link_click_count = models.IntegerField(
        "Nombre de structures cliquées", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_detail_display_count = models.IntegerField(
        "Nombre de structures vues", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_email_link_click_or_detail_display_count = models.IntegerField(
        "Nombre de structures cliquées ou vues", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_detail_contact_click_count = models.IntegerField(
        "Nombre de structures intéressées", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_detail_cocontracting_click_count = models.IntegerField(
        "Nombre de structures ouvertes à la co-traitance", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    siae_detail_not_interested_click_count = models.IntegerField(
        "Nombre de structures pas intéressées", help_text=RECALCULATED_FIELD_HELP_TEXT, default=0
    )
    published_at = models.DateTimeField("Date de publication", blank=True, null=True)
    siae_list_last_seen_date = models.DateTimeField(
        "Date de dernière visite de l'auteur sur la page 'structures intéressées'", blank=True, null=True
    )
    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)
    source = models.CharField(
        verbose_name="Source",
        max_length=20,
        choices=tender_constants.SOURCE_CHOICES,
        default=tender_constants.SOURCE_FORM,
    )
    version = models.PositiveIntegerField(verbose_name="Version", default=1)
    extra_data = models.JSONField(verbose_name="Données complémentaires", editable=False, default=dict)
    import_raw_object = models.JSONField(verbose_name="Données d'import", editable=False, null=True)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(TenderQuerySet)()

    class Meta:
        verbose_name = "Besoin d'achat"
        verbose_name_plural = "Besoins d'achat"
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
        """
        siae_found_list = Siae.objects.filter_with_tender(self)
        self.siaes.set(siae_found_list, clear=False)

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
    def contact_full_name(self) -> str:
        return f"{self.contact_first_name} {self.contact_last_name}"

    def contact_company_name_display(self) -> str:
        if self.contact_company_name:
            return self.contact_company_name
        elif self.author.company_name:
            return self.author.company_name
        return ""

    def sectors_list(self):
        return self.sectors.form_filter_queryset().values_list("name", flat=True)

    def sectors_list_string(self, display_max=3) -> str:
        sectors_name_list = self.sectors_list()
        if display_max and len(sectors_name_list) > display_max:
            sectors_name_list = sectors_name_list[:display_max]
            sectors_name_list.append("…")
        return ", ".join(sectors_name_list)

    def sectors_full_list_string(self) -> str:
        return self.sectors_list_string(display_max=None)

    def perimeters_list(self):
        return self.perimeters.values_list("name", flat=True)

    @cached_property
    def perimeters_list_string(self) -> str:
        return ", ".join(self.perimeters_list())

    @cached_property
    def location_display(self) -> str:
        if self.is_country_area:
            return "France entière"
        elif self.location:
            return self.location.name_display
        else:
            # maintain legacy perimeters display
            return self.perimeters_list_string

    @cached_property
    def amount_display(self) -> str:
        if not self.accept_share_amount:
            return "Non renseigné"
        elif self.amount_exact:
            return f"{self.amount_exact} €"
        elif self.amount:
            return self.get_amount_display()
        else:
            return "Non renseigné"

    def questions_list(self):
        return list(self.questions.values("id", "text"))

    @cached_property
    def external_link_title(self) -> str:
        if self.kind == tender_constants.KIND_TENDER:
            return "Voir l'appel d'offres"
        return "Lien partagé"

    @property
    def cta_card_title_text(self) -> str:
        if self.kind == tender_constants.KIND_TENDER:
            return "Cet appel d'offres vous intéresse ?"
        elif self.kind == tender_constants.KIND_QUOTE:
            return "Cette demande de devis vous intéresse ?"
        elif self.kind == tender_constants.KIND_PROJECT:
            return "Cette consultation vous intéresse ?"
        # just in case
        return "Cette opportunité vous intéresse ?"

    @property
    def cta_card_paragraph_text(self):
        if self.kind == tender_constants.KIND_TENDER:
            return "Accéder à l'appel d'offres afin d'y répondre."
        elif self.kind == tender_constants.KIND_QUOTE:
            return "Accéder aux coordonnées du client afin de lui envoyer un devis."
        elif self.kind == tender_constants.KIND_PROJECT and self.response_is_anonymous:
            return "Manifestez votre intérêt au client. S'il est intéressé, le client vous recontactera via les coordonnées présentes sur votre fiche commerciale."  # noqa
        elif self.kind == tender_constants.KIND_PROJECT:
            return "Accéder aux coordonnées du client afin de lui présenter vos services et produits."
        # just in case
        return "Accédez aux coordonnées de ce client afin de prendre contact avec lui."

    @property
    def cta_card_button_text(self):
        if self.kind == tender_constants.KIND_TENDER:
            return "Voir l'appel d'offres"
        elif self.kind == tender_constants.KIND_PROJECT and self.response_is_anonymous:
            return "Je suis intéressé !"
        return "Accéder aux coordonnées"

    @cached_property
    def can_display_contact_email(self):
        return (tender_constants.RESPONSE_KIND_EMAIL in self.response_kind) and self.contact_email

    @cached_property
    def can_display_contact_phone(self):
        return (tender_constants.RESPONSE_KIND_TEL in self.response_kind) and self.contact_phone

    @cached_property
    def can_display_contact_external_link(self):
        return (tender_constants.RESPONSE_KIND_EXTERNAL in self.response_kind) and self.external_link

    @cached_property
    def response_kind_is_only_external(self):
        return (len(self.response_kind) == 1) and self.can_display_contact_external_link

    @cached_property
    def accept_share_amount_display(self):
        if self.accept_share_amount:
            return tender_constants.ACCEPT_SHARE_AMOUNT_TRUE
        return tender_constants.ACCEPT_SHARE_AMOUNT_FALSE

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
    def siae_email_send_date_count(self):
        return self.tendersiae_set.filter(email_send_date__isnull=False).count()

    @property
    def siae_email_link_click_date_or_detail_display_date_count(self):
        return self.tendersiae_set.filter(
            Q(email_link_click_date__isnull=False) | Q(detail_display_date__isnull=False)
        ).count()

    @property
    def siae_detail_contact_click_date_count(self):
        return self.tendersiae_set.filter(detail_contact_click_date__isnull=False).count()

    @property
    def siae_detail_cocontracting_click_date_count(self):
        return self.tendersiae_set.filter(detail_cocontracting_click_date__isnull=False).count()

    @property
    def siae_detail_not_interested_click_date_count(self):
        return self.tendersiae_set.filter(detail_not_interested_click_date__isnull=False).count()

    def get_absolute_url(self):
        return reverse("tenders:detail", kwargs={"slug": self.slug})

    def set_hubspot_id(self, hubspot_deal_id, with_save=True):
        self.extra_data.update({"hubspot_deal_id": hubspot_deal_id})
        if with_save:
            self.save()

    @property
    def is_draft(self) -> bool:
        return self.status == tender_constants.STATUS_DRAFT

    @property
    def is_pending_validation(self) -> bool:
        return self.status == tender_constants.STATUS_PUBLISHED

    @property
    def is_validated(self) -> bool:
        return bool(self.validated_at) and self.status == tender_constants.STATUS_VALIDATED

    @property
    def is_pending_validation_or_validated(self) -> bool:
        return self.is_pending_validation or self.is_validated

    @property
    def is_sent(self) -> bool:
        return bool(self.first_sent_at) and self.status == tender_constants.STATUS_SENT

    @property
    def is_validated_or_sent(self) -> bool:
        return self.is_validated or self.is_sent

    def set_validated(self):
        self.validated_at = timezone.now()
        self.status = tender_constants.STATUS_VALIDATED
        log_item = {
            "action": "validate",
            "date": self.validated_at.isoformat(),
        }
        self.logs.append(log_item)
        self.save()

    def set_sent(self):
        if not self.first_sent_at:
            self.first_sent_at = timezone.now()
            self.status = tender_constants.STATUS_SENT

        self.last_sent_at = timezone.now()
        log_item = {
            "action": "send",
            "date": self.last_sent_at.isoformat(),
        }
        self.logs.append(log_item)
        self.save()


class TenderSiaeQuerySet(models.QuerySet):
    def email_click_reminder(self, gte_days_ago, lt_days_ago):
        return (
            self.filter(email_send_date__gte=gte_days_ago)
            .filter(email_send_date__lt=lt_days_ago)
            .filter(email_link_click_date__isnull=True)
            .filter(detail_display_date__isnull=True)
            .filter(detail_contact_click_date__isnull=True)
        )

    def detail_contact_click_post_reminder(self, gte_days_ago, lt_days_ago):
        return self.filter(detail_contact_click_date__gte=gte_days_ago).filter(
            detail_contact_click_date__lt=lt_days_ago
        )


class TenderQuestion(models.Model):
    text = models.TextField(verbose_name="Intitulé de la question", blank=False)

    tender = models.ForeignKey(
        "tenders.Tender", verbose_name="Besoin d'achat", related_name="questions", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Question de l'acheteur"
        verbose_name_plural = "Questions de l'acheteur"

    def __str__(self):
        return self.text


class TenderSiae(models.Model):
    TENDER_SIAE_SOURCE_EMAIL = "EMAIL"
    TENDER_SIAE_SOURCE_DASHBOARD = "DASHBOARD"
    TENDER_SIAE_SOURCE_LINK = "LINK"
    TENDER_SIAE_SOURCE_CHOICES = (
        (TENDER_SIAE_SOURCE_EMAIL, "E-mail"),
        (TENDER_SIAE_SOURCE_DASHBOARD, "Dashboard"),
        (TENDER_SIAE_SOURCE_LINK, "Lien"),
    )

    tender = models.ForeignKey("tenders.Tender", verbose_name="Besoin d'achat", on_delete=models.CASCADE)
    siae = models.ForeignKey("siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE)

    source = models.CharField(max_length=20, choices=TENDER_SIAE_SOURCE_CHOICES, default=TENDER_SIAE_SOURCE_EMAIL)

    # stats
    email_send_date = models.DateTimeField("Date d'envoi de l'e-mail", blank=True, null=True)
    email_link_click_date = models.DateTimeField("Date de clic sur le lien dans l'e-mail", blank=True, null=True)
    detail_display_date = models.DateTimeField("Date de visualisation du besoin", blank=True, null=True)
    detail_contact_click_date = models.DateTimeField(
        "Date de clic sur les coordonnées du besoin", blank=True, null=True
    )
    detail_cocontracting_click_date = models.DateTimeField(
        "Date de clic sur Répondre en co-traitance", blank=True, null=True
    )
    detail_not_interested_click_date = models.DateTimeField("Date de clic sur Pas intéressé", blank=True, null=True)
    logs = models.JSONField(verbose_name="Logs historiques", editable=False, default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)

    objects = models.Manager.from_queryset(TenderSiaeQuerySet)()

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
                amount_index = tender_constants.AMOUNT_RANGE_CHOICE_LIST.index(tender.amount)
                conditions |= Q(amount_in__in=tender_constants.AMOUNT_RANGE_CHOICE_LIST[amount_index:])
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

    # admin
    notes = GenericRelation("notes.Note", related_query_name="partner_share_tender")

    # stats
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


class TenderStepsData(models.Model):
    FIELDS_TO_REDACT = [
        "contact-contact_email",
        "contact-contact_phone",
        "contact-contact_last_name",
        "contact-contact_first_name",
    ]

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)
    uuid = ShortUUIDField(
        verbose_name="Identifiant UUID",
        default=uuid,
        editable=False,
        unique=True,
        db_index=True,
        auto_created=True,
    )
    steps_data = models.JSONField(verbose_name="Données des étapes", editable=False, default=list)

    class Meta:
        verbose_name = "Besoin d'achat - Données des étapes"
        verbose_name_plural = "Besoins d'achat - Données des étapes"

    def __str__(self):
        return f"{self.uuid} - {self.created_at}"
