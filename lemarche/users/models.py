from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

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

    KIND_PERSO = "PERSO"  # PERSON_TYPE_NATURAL / 1
    KIND_COMPANY = "COMPANY"  # PERSON_TYPE_LEGAL / 2 (not used)
    KIND_BUYER = "BUYER"  # PERSON_TYPE_CLASSIC / 3
    KIND_SIAE = "SIAE"  # PERSON_TYPE_INCLUSIVE / 4
    KIND_ADMIN = "ADMIN"  # PERSON_TYPE_ADMIN/ 5
    KIND_PARTNER = "PARTNER"  # PERSON_TYPE_PARTNER / 6

    KIND_CHOICES = (
        (KIND_PERSO, "Une personne"),
        (KIND_COMPANY, "Une entreprise"),
        (KIND_BUYER, "Un acheteur qui souhaite réaliser un achat inclusif"),
        (KIND_SIAE, "Structure inclusive qui souhaite proposer ses offres"),
        (KIND_ADMIN, "Administrateur.trice"),
        (KIND_PARTNER, "Partenaire")
    )

    username = None
    email = models.EmailField(verbose_name="E-mail", unique=True)
    first_name = models.CharField("Prénom", max_length=150)
    last_name = models.CharField("Nom", max_length=150)

    kind = models.CharField(verbose_name="Type", max_length=20, choices=KIND_CHOICES, default=KIND_PERSO)

    phone = models.CharField(verbose_name="Téléphone", max_length=20, blank=True, null=True)
    website = models.URLField(verbose_name="Site web", blank=True, null=True)
    company_name = models.CharField(verbose_name="Nom de l'entreprise", max_length=255, blank=True, null=True)
    siret = models.CharField(verbose_name="Siret ou Siren", max_length=14, blank=True, null=True)
    naf = models.CharField(verbose_name="Naf", max_length=5, blank=True, null=True)

    api_key = models.CharField(verbose_name="Clé API", max_length=128, unique=True, blank=True, null=True)

    c1_id = models.IntegerField(blank=True, null=True)

    # is_active, is_staff, is_superuser

    # date_joined, last_login
    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de mise à jour", auto_now=True)

    def __str__(self):
        return self.email
