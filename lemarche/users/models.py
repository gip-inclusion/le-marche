from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.functions import RandomUUID
from django.db import models
from django.db.models import Count, F, Value
from django.db.models.functions import Concat, Greatest, Lower
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from lemarche.stats.models import StatsUser
from lemarche.users import constants as user_constants
from lemarche.utils.data import phone_number_display
from lemarche.utils.emails import anonymize_email


class UserQueryset(models.QuerySet):
    """
    Custom queryset with additional filtering methods for users.
    """

    def is_admin_bizdev(self):
        return self.filter(kind=user_constants.KIND_ADMIN, position__iexact="Bizdev", is_staff=True)

    def has_company(self):
        return self.filter(company__isnull=False).distinct()

    def has_siae(self):
        return self.filter(siaes__isnull=False).distinct()

    def has_tender(self):
        return self.filter(tenders__isnull=False).distinct()

    def has_favorite_list(self):
        return self.filter(favorite_lists__isnull=False).distinct()

    def has_partner_network(self):
        return self.filter(partner_network__isnull=False)

    def has_api_key(self):
        return self.filter(api_key__isnull=False)

    def has_email_domain(self, email_domain):
        if not email_domain.startswith("@"):
            email_domain = f"@{email_domain}"
        return self.filter(email__iendswith=email_domain)

    def with_siae_stats(self):
        return self.prefetch_related("siaes").annotate(siae_count_annotated=Count("siaes", distinct=True))

    def with_tender_stats(self):
        return self.prefetch_related("tenders").annotate(tender_count_annotated=Count("tenders", distinct=True))

    def with_latest_activities(self):
        return self.annotate(
            latest_activity_at=Greatest(
                "updated_at", "last_login", "dashboard_last_seen_date", "tender_list_last_seen_date"
            )
        )

    def anonymize_update(self):
        """Wipe or replace personal data stored on User model only"""
        return self.update(
            is_active=False,  # inactive users are allowed to log in standard login views
            is_anonymized=True,
            email=Concat(F("id"), Value("@domain.invalid")),
            first_name="",
            last_name="",
            phone="",
            api_key=None,
            api_key_last_updated=None,
            # https://docs.djangoproject.com/en/5.1/ref/contrib/auth/#django.contrib.auth.models.User.set_unusable_password
            # Imitating the method but in sql. Prevent password reset attempt
            # Random string is to avoid chances of impersonation by admins https://code.djangoproject.com/ticket/20079
            password=Concat(Value(UNUSABLE_PASSWORD_PREFIX), RandomUUID()),
        )


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def get_queryset(self):
        return UserQueryset(self.model, using=self._db)

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError("Il manque le champ E-mail")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superuser doit avoir is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def is_admin_bizdev(self):
        return self.get_queryset().is_admin_bizdev()

    def has_company(self):
        return self.get_queryset().has_company()

    def has_siae(self):
        return self.get_queryset().has_siae()

    def has_tender(self):
        return self.get_queryset().has_tender()

    def has_favorite_list(self):
        return self.get_queryset().has_favorite_list()

    def has_partner_network(self):
        return self.get_queryset().has_partner_network()

    def has_api_key(self):
        return self.get_queryset().has_api_key()

    def has_email_domain(self, email_domain):
        return self.get_queryset().has_email_domain(email_domain)

    def with_siae_stats(self):
        return self.get_queryset().with_siae_stats()

    def with_tender_stats(self):
        return self.get_queryset().with_tender_stats()


class User(AbstractUser):
    """
    C4 Custom User Model
    """

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_EMAIL_REQUIRED = True

    TRACK_UPDATE_FIELDS = [
        # set last_updated fields
        "api_key",
    ]

    FIELDS_STATS_COUNT = ["favorite_list_count"]
    FIELDS_STATS_TIMESTAMPS = [
        "api_key_last_updated",
        "dashboard_last_seen_date",
        "tender_list_last_seen_date",
        "date_joined",
        "last_login",
        "created_at",
        "updated_at",
    ]
    READONLY_FIELDS = FIELDS_STATS_COUNT + FIELDS_STATS_TIMESTAMPS

    # used in templates
    KIND_SIAE = user_constants.KIND_SIAE
    KIND_BUYER = user_constants.KIND_BUYER
    KIND_PARTNER = user_constants.KIND_PARTNER
    KIND_INDIVIDUAL = user_constants.KIND_INDIVIDUAL
    KIND_ADMIN = user_constants.KIND_ADMIN

    username = None
    email = models.EmailField(
        verbose_name="Adresse e-mail",
        unique=True,
        error_messages={"unique": "Cette adresse e-mail est déjà utilisée."},
    )
    first_name = models.CharField(verbose_name="Prénom", max_length=150)
    last_name = models.CharField(verbose_name="Nom", max_length=150)
    kind = models.CharField(
        verbose_name="Type", max_length=20, choices=user_constants.KIND_CHOICES_WITH_ADMIN, blank=True
    )
    phone = PhoneNumberField(verbose_name="Téléphone", max_length=20, blank=True)

    company = models.ForeignKey(
        "companies.Company",
        verbose_name="Entreprise",
        related_name="users",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    company_name = models.CharField(verbose_name="Nom de l'entreprise", max_length=255, blank=True)

    position = models.CharField(verbose_name="Poste", max_length=255, blank=True)
    buyer_kind = models.CharField(
        verbose_name="Type d'acheteur", max_length=20, choices=user_constants.BUYER_KIND_CHOICES, blank=True
    )
    buyer_kind_detail = models.CharField(
        verbose_name="Type d'acheteur (détail)",
        max_length=20,
        choices=user_constants.BUYER_KIND_DETAIL_CHOICES,
        blank=True,
    )
    partner_kind = models.CharField(
        verbose_name="Type de partenaire", max_length=20, choices=user_constants.PARTNER_KIND_CHOICES, blank=True
    )
    partner_network = models.ForeignKey(
        "networks.Network",
        verbose_name="Réseau du partenaire",
        related_name="user_partners",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sectors = models.ManyToManyField(
        "sectors.Sector",
        verbose_name="Secteurs d'activité",
        related_name="users",
        blank=True,
        help_text="Quelles sont les familles d’achat sur lesquelles vous travaillez ?",
    )

    can_display_tender_contact_details = models.BooleanField(
        verbose_name="Ce partenaire a accès aux coordonnées de l'acheteur ?",
        help_text="Permet à certains utilisateurs partenaires de voir directement les coordonnées. Les autres auront un message leur demandant de contacter les admins",  # noqa
        default=False,
    )

    source = models.CharField(
        max_length=20, choices=user_constants.SOURCE_CHOICES, default=user_constants.SOURCE_SIGNUP_FORM
    )

    api_key = models.CharField(verbose_name="Clé API", max_length=128, unique=True, blank=True, null=True)
    api_key_last_updated = models.DateTimeField(
        verbose_name="Date de dernière mise à jour de la clé API", blank=True, null=True
    )

    accept_rgpd = models.BooleanField(default=False)
    accept_survey = models.BooleanField(
        help_text="J'accepte de répondre à une enquête deux fois par an afin de permettre de mesurer la progression des achats inclusifs en France",  # noqa
        default=False,
    )
    accept_offers_for_pro_sector = models.BooleanField(
        help_text="Je m'engage à ce que les offres déposées sur la Place de marché soient destinées à des structures professionnelles (association, secteur privé ou public)",  # noqa
        default=False,
    )
    accept_quote_promise = models.BooleanField(
        help_text="Je m'engage à traiter les demandes de devis qui me seront adressées (soumettre un devis, solliciter des informations complémentaires ou  refuser une demande constituent des réponses)",  # noqa
        default=False,
    )

    accept_share_contact_to_external_partners = models.BooleanField(
        verbose_name="Partage de contact à des partenaires externes",
        help_text="J'accepte que mes coordonnées de contact soient partagées avec les partenaires externes du Marché de l'inclusion afin de recevoir des opportunités commerciales (appels d'offres, marché ...)",  # noqa
        default=False,
    )

    # services data
    brevo_contact_id = models.PositiveIntegerField("Brevo contact id", blank=True, null=True)

    # admin
    notes = GenericRelation("notes.Note", related_query_name="user")

    # stats
    favorite_list_count = models.IntegerField("Nombre de listes de favoris", default=0)
    dashboard_last_seen_date = models.DateTimeField(
        "Date de dernière visite sur la page 'tableau de bord'", blank=True, null=True
    )
    tender_list_last_seen_date = models.DateTimeField(
        "Date de dernière visite sur la page 'besoins'", blank=True, null=True
    )
    extra_data = models.JSONField(verbose_name="Données complémentaires", editable=False, default=dict)
    recipient_transactional_send_logs = GenericRelation(
        "conversations.TemplateTransactionalSendLog",
        related_query_name="user",
        content_type_field="recipient_content_type",
        object_id_field="recipient_object_id",
    )

    # is_active, is_staff, is_superuser
    is_anonymized = models.BooleanField(verbose_name="L'utilisateur à été anonymisé", default=False)

    # date_joined, last_login
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de mise à jour", auto_now=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="user_email_ci_uniqueness",
                violation_error_message="Cette adresse e-mail est déjà utilisée.",
            ),
        ]

    def __str__(self):
        return self.email

    def __init__(self, *args, **kwargs):
        """
        https://stackoverflow.com/a/23363123
        """
        super(User, self).__init__(*args, **kwargs)
        for field_name in self.TRACK_UPDATE_FIELDS:
            setattr(self, f"__previous_{field_name}", getattr(self, field_name))

    def set_last_updated_fields(self):
        """
        We track changes on some fields, in order to update their 'last_updated' counterpart.
        Where are the '__previous' fields set? In the __init__ method
        """
        for field_name in self.TRACK_UPDATE_FIELDS:
            previous_field_name = f"__previous_{field_name}"
            if getattr(self, field_name) and getattr(self, field_name) != getattr(self, previous_field_name):
                try:
                    setattr(self, f"{field_name}_last_updated", timezone.now())
                except AttributeError:  # TRACK_UPDATE_FIELDS without last_updated fields
                    pass

    def save(self, *args, **kwargs):
        """
        - update the "last_updated" fields
        """
        self.set_last_updated_fields()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name.upper()[:1]}. {self.last_name.upper()}"
        return ""

    @property
    def email_anonymized(self):
        return anonymize_email(self.email)

    @property
    def kind_detail_display(self):
        kind_detail_display_string = ""
        if self.kind:
            kind_detail_display_string += self.get_kind_display()
        if self.buyer_kind_detail:
            # remove parenthesis suffix
            kind_detail_display_string += f" : {self.get_buyer_kind_detail_display().split(' (', 1)[0]}"
        elif self.partner_kind:
            kind_detail_display_string += f" : {self.get_partner_kind_display()}"
        return kind_detail_display_string

    @property
    def phone_display(self):
        return phone_number_display(self.phone)

    @property
    def has_siae(self):
        return self.siaes.exists()

    @property
    def is_buyer(self):
        return self.kind == self.KIND_BUYER

    @property
    def is_buyer_pro(self):
        return (
            self.is_buyer
            and self.buyer_kind_detail
            and (
                self.buyer_kind_detail
                not in [
                    user_constants.BUYER_KIND_DETAIL_PRIVATE_TPE,
                    user_constants.BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION,
                ]
            )
        )

    @property
    def is_admin(self) -> bool:
        return self.kind == self.KIND_ADMIN

    def has_tender_siae(self, tender=None):
        from lemarche.tenders.models import TenderSiae

        qs = TenderSiae.objects.filter(siae__in=self.siaes.all())
        if tender:
            qs = qs.filter(tender=tender)
        return qs.exists()

    @property
    def tender_siae_unread_count(self):
        from lemarche.tenders.models import Tender

        return Tender.objects.unread(self).count()


@receiver(pre_save, sender=User)
def update_api_key_last_update(sender, instance, **kwargs):
    """
    Before saving a user, add the to `api_key_last_updated`
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.api_key != instance.api_key:
                instance.api_key_last_updated = timezone.now()
        except sender.DoesNotExist:
            if instance.api_key:
                instance.api_key_last_updated = timezone.now()
    elif instance.api_key:
        instance.api_key_last_updated = timezone.now()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    if settings.BITOUBI_ENV == "prod":
        list_stats_attrs = [field.name for field in StatsUser._meta.fields]
        StatsUser.objects.update_or_create(id=instance.pk, defaults=model_to_dict(instance, fields=list_stats_attrs))
