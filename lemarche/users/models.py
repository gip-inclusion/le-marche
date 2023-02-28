from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone

from lemarche.stats.models import StatsUser
from lemarche.utils import constants


class UserQueryset(models.QuerySet):
    """
    Custom queryset with additional filtering methods for users.
    """

    def has_siae(self):
        """Only return users who are linked to Siae(s)."""
        return self.filter(siaes__isnull=False).distinct()

    def has_tender(self):
        """Only return users who have Tender(s)."""
        return self.filter(tenders__isnull=False).distinct()

    def has_favorite_list(self):
        """Only return users who have FavoriteList(s)."""
        return self.filter(favorite_lists__isnull=False).distinct()

    def has_partner_network(self):
        return self.filter(partner_network__isnull=False)

    def has_api_key(self):
        return self.filter(api_key__isnull=False)


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

    def has_siae(self):
        """Only return users who are linked to Siae(s)."""
        return self.get_queryset().has_siae()

    def has_tender(self):
        """Only return users who have Tender(s)."""
        return self.get_queryset().has_tender()

    def has_favorite_list(self):
        """Only return users who have FavoriteList(s)."""
        return self.get_queryset().has_favorite_list()

    def has_partner_network(self):
        return self.get_queryset().has_partner_network()

    def has_api_key(self):
        return self.get_queryset().has_api_key()


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

    # used in templates
    KIND_SIAE = constants.USER_KIND_SIAE
    KIND_BUYER = constants.USER_KIND_BUYER
    KIND_PARTNER = constants.USER_KIND_PARTNER
    KIND_ADMIN = constants.USER_KIND_ADMIN

    BUYER_KIND_PUBLIC = "PUBLIC"
    BUYER_KIND_PRIVATE = "PRIVE"
    BUYER_KIND_CHOICES = (
        (BUYER_KIND_PUBLIC, "Public"),
        (BUYER_KIND_PRIVATE, "Privé"),
    )
    BUYER_KIND_DETAIL_PUBLIC_MINISTRY = "PUBLIC_MINISTRY"
    BUYER_KIND_DETAIL_PUBLIC_ESTABLISHMENT = "PUBLIC_ESTABLISHMENT"
    BUYER_KIND_DETAIL_PUBLIC_COLLECTIVITY = "PUBLIC_COLLECTIVITY"
    BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION = "PUBLIC_ASSOCIATION"
    BUYER_KIND_DETAIL_PRIVATE_BIG_CORP = "PRIVATE_BIG_CORP"
    BUYER_KIND_DETAIL_PRIVATE_ETI = "PRIVATE_ETI"
    BUYER_KIND_DETAIL_PRIVATE_PME = "PRIVATE_PME"
    BUYER_KIND_DETAIL_PRIVATE_TPE = "PRIVATE_TPE"
    BUYER_KIND_DETAIL_CHOICES = (
        (BUYER_KIND_DETAIL_PUBLIC_MINISTRY, "Public : Ministère"),
        (BUYER_KIND_DETAIL_PUBLIC_ESTABLISHMENT, "Public : Établissement public"),
        (BUYER_KIND_DETAIL_PUBLIC_COLLECTIVITY, "Public : Collectivité"),
        (BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION, "Public : Association"),
        (BUYER_KIND_DETAIL_PRIVATE_BIG_CORP, "Privé : Grand groupe"),
        (BUYER_KIND_DETAIL_PRIVATE_ETI, "Privé : ETI"),
        (BUYER_KIND_DETAIL_PRIVATE_PME, "Privé : PME"),
        (BUYER_KIND_DETAIL_PRIVATE_TPE, "Privé : TPE"),
    )

    PARTNER_KIND_FACILITATOR = "FACILITATEUR"
    PARTNER_KIND_NETWORD_IAE = "RESEAU_IAE"
    PARTNER_KIND_NETWORK_HANDICAP = "RESEAU_HANDICAP"
    PARTNER_KIND_DREETS = "DREETS"
    PARTNER_KIND_PRESCRIBER = "PRESCRIPTEUR"
    PARTNER_KIND_PUBLIC = "PUBLIC"
    PARTNER_KIND_PRIVATE = "PRIVE"
    PARTNER_KIND_OTHER = "AUTRE"
    PARTNER_KIND_CHOICES = (
        (PARTNER_KIND_FACILITATOR, "Facilitateur des clauses sociales"),
        (PARTNER_KIND_NETWORD_IAE, "Réseaux IAE"),
        (PARTNER_KIND_NETWORK_HANDICAP, "Réseau secteur Handicap"),
        (PARTNER_KIND_DREETS, "DREETS / DDETS"),
        (PARTNER_KIND_PRESCRIBER, "Prescripteur"),
        (PARTNER_KIND_PUBLIC, "Organisme public"),
        (PARTNER_KIND_PRIVATE, "Organisme privé"),
        (PARTNER_KIND_OTHER, "Autre"),
    )

    SOURCE_SIGNUP_FORM = "SIGNUP_FORM"
    SOURCE_TENDER_FORM = "TENDER_FORM"
    SOURCE_DJANGO_ADMIN = "DJANGO_ADMIN"

    SOURCE_CHOICES = (
        (SOURCE_SIGNUP_FORM, "Formulaire d'inscription"),
        (SOURCE_TENDER_FORM, "Formulaire de dépôt de besoin"),
        (SOURCE_DJANGO_ADMIN, "Admin Django"),
    )

    username = None
    email = models.EmailField(verbose_name="Adresse e-mail", unique=True)
    first_name = models.CharField(verbose_name="Prénom", max_length=150)
    last_name = models.CharField(verbose_name="Nom", max_length=150)
    kind = models.CharField(
        verbose_name="Type", max_length=20, choices=constants.USER_KIND_CHOICES_WITH_ADMIN, blank=True
    )
    phone = models.CharField(verbose_name="Téléphone", max_length=20, blank=True)
    company_name = models.CharField(verbose_name="Nom de l'entreprise", max_length=255, blank=True)
    position = models.CharField(verbose_name="Poste", max_length=255, blank=True)
    buyer_kind = models.CharField(
        verbose_name="Type d'acheteur", max_length=20, choices=BUYER_KIND_CHOICES, blank=True
    )
    buyer_kind_detail = models.CharField(
        verbose_name="Type d'acheteur (détail)", max_length=20, choices=BUYER_KIND_DETAIL_CHOICES, blank=True
    )
    partner_kind = models.CharField(
        verbose_name="Type de partenaire", max_length=20, choices=PARTNER_KIND_CHOICES, blank=True
    )
    partner_network = models.ForeignKey(
        "networks.Network",
        verbose_name="Réseau du partenaire",
        related_name="user_partners",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    can_display_tender_contact_details = models.BooleanField(
        verbose_name="Ce partenaire a accès aux coordonnées de l'acheteur ?",
        help_text="Permet à certains utilisateurs partenaires de voir directement les coordonnées. Les autres auront un message leur demandant de contacter les admins",  # noqa
        default=False,
    )

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_SIGNUP_FORM)

    api_key = models.CharField(verbose_name="Clé API", max_length=128, unique=True, blank=True, null=True)
    api_key_last_updated = models.DateTimeField(
        verbose_name="Date de dernière mise à jour de la clé API", blank=True, null=True
    )

    accept_rgpd = models.BooleanField(help_text="J'accepte les conditions d'utilisation du service", default=False)
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

    image_name = models.CharField(verbose_name="Nom de l'image", max_length=255, blank=True)
    image_url = models.URLField(verbose_name="Lien vers l'image", max_length=500, blank=True)

    c4_id = models.IntegerField(blank=True, null=True)
    c4_phone_prefix = models.CharField(verbose_name="Indicatif international", max_length=20, blank=True)
    c4_time_zone = models.CharField(verbose_name="Fuseau", max_length=150, blank=True)
    c4_website = models.URLField(verbose_name="Site web", blank=True)
    c4_siret = models.CharField(verbose_name="Siret ou Siren", max_length=14, blank=True)
    c4_naf = models.CharField(verbose_name="Naf", max_length=5, blank=True)
    c4_phone_verified = models.BooleanField(default=False)
    c4_email_verified = models.BooleanField(default=False)
    c4_id_card_verified = models.BooleanField(default=False)

    # stats
    dashboard_last_seen_date = models.DateTimeField(
        "Date de dernière visite sur la page 'tableau de bord'", blank=True, null=True
    )
    tender_list_last_seen_date = models.DateTimeField(
        "Date de dernière visite sur la page 'besoins'", blank=True, null=True
    )
    extra_data = models.JSONField(verbose_name="Données complémentaires", editable=False, default=dict)

    # is_active, is_staff, is_superuser

    # date_joined, last_login
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de mise à jour", auto_now=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

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
        self.set_last_updated_fields()
        super().save(*args, **kwargs)

    def set_hubspot_id(self, hubspot_contact_id, with_save=True):
        self.extra_data.update({"hubspot_contact_id": hubspot_contact_id})
        if with_save:
            self.save()

    @property
    def hubspot_contact_id(self):
        return self.extra_data.get("hubspot_contact_id")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name.upper()[:1]}. {self.last_name.upper()}"
        return ""

    @property
    def kind_detail_display(self):
        kind_detail_display_string = ""
        if self.kind:
            kind_detail_display_string += self.get_kind_display()
        if self.buyer_kind_detail:
            kind_detail_display_string += f" : {self.get_buyer_kind_detail_display()}"
        elif self.partner_kind:
            kind_detail_display_string += f" : {self.get_partner_kind_display()}"
        return kind_detail_display_string

    @property
    def has_siae(self):
        return self.siaes.exists()

    def has_tender_siae(self, tender=None):
        from lemarche.tenders.models import TenderSiae

        qs = TenderSiae.objects.filter(siae__in=self.siaes.all())
        if tender:
            qs = qs.filter(tender=tender)
        return qs.exists()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    if settings.BITOUBI_ENV == "prod":
        list_stats_attrs = [field.name for field in StatsUser._meta.fields]
        StatsUser.objects.update_or_create(id=instance.pk, defaults=model_to_dict(instance, fields=list_stats_attrs))
