from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.measure import D
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.constants import DEPARTMENTS_PRETTY, REGIONS, REGIONS_PRETTY, get_department_code_from_name
from lemarche.siaes.validators import validate_naf, validate_post_code, validate_siret


class SiaeQuerySet(models.QuerySet):
    def is_live(self):
        return self.filter(is_active=True).filter(is_delisted=False)

    def is_not_live(self):
        return self.filter(Q(is_active=False) | Q(is_delisted=True))

    def has_user(self):
        """Only return siaes who have at least 1 user."""
        return self.filter(users__isnull=False)

    def in_region(self, **kwargs):
        if "name" in kwargs:
            return self.filter(region=kwargs["name"])
        if "code" in kwargs:
            code_clean = kwargs["code"].strip("R")  # "R" ? see Perimeter model & import_region.py
            region_name = REGIONS.get(code_clean)
            return self.filter(region=region_name)

    def in_department(self, **kwargs):
        if "name" in kwargs:
            department_code = get_department_code_from_name(kwargs["name"])
            return self.filter(department=department_code)
        if "code" in kwargs:
            return self.filter(department=kwargs["code"])

    def within(self, point, distance_km):
        return self.filter(coords__dwithin=(point, D(km=distance_km)))


class Siae(models.Model):
    READONLY_FIELDS_FROM_C1 = [
        "name",
        "brand",
        "siret",
        "naf",
        "email",
        "phone",
        "kind",
        "nature",  # "website", "presta_type"
        "city",
        "post_code",
        "department",
        "region",
        "coords",
        "admin_name",
        "admin_email",
        "is_delisted",
        "is_active",
        "siret_is_valid",
        "c1_id",
        "c1_source",
        "c4_id",
        "last_sync_date",
    ]
    READONLY_FIELDS_FROM_QPV = ["is_qpv", "qpv_name", "qpv_code"]
    READONLY_FIELDS_FROM_APIGOUV = ["ig_employees", "ig_ca", "ig_date_constitution"]
    READONLY_FIELDS = READONLY_FIELDS_FROM_C1 + READONLY_FIELDS_FROM_QPV + READONLY_FIELDS_FROM_APIGOUV

    KIND_EI = "EI"
    KIND_AI = "AI"
    KIND_ACI = "ACI"
    KIND_ETTI = "ETTI"
    KIND_EITI = "EITI"
    KIND_GEIQ = "GEIQ"
    KIND_EA = "EA"
    KIND_EATT = "EATT"

    KIND_CHOICES = (
        (KIND_EI, "Entreprise d'insertion"),  # Regroupées au sein de la fédération des entreprises d'insertion.
        (KIND_AI, "Association intermédiaire"),
        (KIND_ACI, "Atelier chantier d'insertion"),
        # (KIND_ACIPHC, "Atelier chantier d'insertion premières heures en chantier"),
        (KIND_ETTI, "Entreprise de travail temporaire d'insertion"),
        (KIND_EITI, "Entreprise d'insertion par le travail indépendant"),
        (KIND_GEIQ, "Groupement d'employeurs pour l'insertion et la qualification"),
        (KIND_EA, "Entreprise adaptée"),
        (KIND_EATT, "Entreprise adaptée de travail temporaire"),
    )

    SOURCE_ASP = "ASP"
    SOURCE_GEIQ = "GEIQ"
    SOURCE_EA_EATT = "EA_EATT"
    SOURCE_USER_CREATED = "USER_CREATED"
    SOURCE_STAFF_CREATED = "STAFF_CREATED"

    SOURCE_CHOICES = (
        (SOURCE_ASP, "Export ASP"),
        (SOURCE_GEIQ, "Export GEIQ"),
        (SOURCE_EA_EATT, "Export EA+EATT"),
        (SOURCE_USER_CREATED, "Utilisateur (Antenne)"),
        (SOURCE_STAFF_CREATED, "Staff Itou"),
    )

    NATURE_HEAD_OFFICE = "HEAD_OFFICE"
    NATURE_ANTENNA = "ANTENNA"

    NATURE_CHOICES = (
        (NATURE_HEAD_OFFICE, "Conventionné avec la Direccte"),
        (NATURE_ANTENNA, "Rattaché à un autre conventionnement"),
    )

    PRESTA_DISP = "DISP"
    PRESTA_PREST = "PREST"
    PRESTA_BUILD = "BUILD"

    PRESTA_CHOICES = (
        (PRESTA_DISP, "Mise à disposition - Interim"),  # 0010
        (PRESTA_PREST, "Prestation de service"),  # 0100
        (PRESTA_BUILD, "Fabrication et commercialisation de biens"),  # 1000
    )

    DEPARTMENT_CHOICES = DEPARTMENTS_PRETTY.items()
    REGION_CHOICES = REGIONS_PRETTY.items()
    GEO_RANGE_COUNTRY = "COUNTRY"  # 3
    GEO_RANGE_REGION = "REGION"  # 2
    GEO_RANGE_DEPARTMENT = "DEPARTMENT"  # 1
    GEO_RANGE_CUSTOM = "CUSTOM"  # 0
    GEO_RANGE_CHOICES = (
        (GEO_RANGE_COUNTRY, "France entière"),
        (GEO_RANGE_REGION, "Région"),
        (GEO_RANGE_DEPARTMENT, "Département"),
        (GEO_RANGE_CUSTOM, "Distance en kilomètres"),
    )

    name = models.CharField(verbose_name="Raison sociale", max_length=255)
    brand = models.CharField(verbose_name="Enseigne", max_length=255, blank=True, null=True)
    kind = models.CharField(verbose_name="Type de structure", max_length=6, choices=KIND_CHOICES, default=KIND_EI)
    description = models.TextField(verbose_name="Description", blank=True)
    siret = models.CharField(verbose_name="Siret", validators=[validate_siret], max_length=14, db_index=True)
    siret_is_valid = models.BooleanField(verbose_name="Siret Valide", default=False)
    naf = models.CharField(verbose_name="Naf", validators=[validate_naf], max_length=5, blank=True, null=True)
    nature = models.CharField(
        verbose_name="Établissement", max_length=20, choices=NATURE_CHOICES, blank=True, null=True
    )
    presta_type = ArrayField(
        verbose_name="Type de prestation",
        base_field=models.CharField(max_length=20, choices=PRESTA_CHOICES),
        blank=True,
        null=True,
    )

    website = models.URLField(verbose_name="Site web", blank=True, null=True)
    email = models.EmailField(verbose_name="E-mail", blank=True, null=True)
    phone = models.CharField(verbose_name="Téléphone", max_length=20, blank=True, null=True)
    address = models.TextField(verbose_name="Adresse")
    city = models.CharField(verbose_name="Ville", max_length=255, blank=True, null=True)
    department = models.CharField(
        verbose_name="Département", max_length=255, choices=DEPARTMENT_CHOICES, blank=True, null=True
    )
    region = models.CharField(verbose_name="Région", max_length=255, choices=REGION_CHOICES, blank=True, null=True)
    post_code = models.CharField(
        verbose_name="Code Postal", validators=[validate_post_code], max_length=5, blank=True, null=True
    )
    # Latitude and longitude coordinates.
    # https://docs.djangoproject.com/en/2.2/ref/contrib/gis/model-api/#pointfield
    coords = gis_models.PointField(geography=True, blank=True, null=True)
    geo_range = models.CharField(
        verbose_name="Périmètre d'intervention", max_length=20, choices=GEO_RANGE_CHOICES, blank=True, null=True
    )
    geo_range_custom_distance = models.IntegerField(
        verbose_name="Distance en kilomètres (périmètre d'intervention)", blank=True, null=True
    )

    is_consortium = models.BooleanField(verbose_name="Consortium", default=False)
    is_cocontracting = models.BooleanField(verbose_name="Co-traitance", default=False)

    is_active = models.BooleanField(verbose_name="Active", default=True)
    is_delisted = models.BooleanField(verbose_name="Masquée", default=False)
    is_first_page = models.BooleanField(verbose_name="A la une", default=False)

    admin_name = models.CharField(max_length=255, blank=True, null=True)
    admin_email = models.EmailField(max_length=255, blank=True, null=True)

    sectors = models.ManyToManyField(
        "sectors.Sector", verbose_name="Secteurs d'activité", related_name="siaes", blank=True
    )
    networks = models.ManyToManyField("networks.Network", verbose_name="Réseaux", related_name="siaes", blank=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="Gestionnaires", related_name="siaes", blank=True
    )
    # ForeignKeys: offers, labels, client_references

    is_qpv = models.BooleanField(verbose_name="Zone QPV", blank=False, null=False, default=False)
    qpv_name = models.CharField(max_length=255, blank=True, null=True)
    qpv_code = models.CharField(max_length=16, blank=True, null=True)

    ig_employees = models.CharField(max_length=255, blank=True, null=True)
    ig_ca = models.IntegerField(blank=True, null=True)
    ig_date_constitution = models.DateTimeField(blank=True, null=True)

    c1_id = models.IntegerField(blank=True, null=True)
    c1_source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, null=True)
    c4_id = models.IntegerField(blank=True, null=True)

    last_sync_date = models.DateTimeField(blank=True, null=True)
    sync_skip = models.BooleanField(blank=False, null=False, default=False)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de mise à jour", auto_now=True)

    objects = models.Manager.from_queryset(SiaeQuerySet)()

    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ["name"]
        permissions = [
            ("access_api", "Can access the API"),
        ]

    def __str__(self):
        return self.name

    @property
    def latitude(self):
        if self.coords:
            return self.coords.y
        return None

    @property
    def longitude(self):
        if self.coords:
            return self.coords.x
        return None

    def sectors_list_to_string(self):
        return ", ".join(self.sectors.all().values_list("name", flat=True))


class SiaeOffer(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)
    description = models.TextField(verbose_name="Description", blank=True)

    siae = models.ForeignKey("siaes.Siae", verbose_name="Structure", related_name="offers", on_delete=models.CASCADE)
    source = models.CharField(verbose_name="Source", max_length=20, blank=True, null=True)  # "listing_import"

    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"

    def __str__(self):
        return self.name


class SiaeLabel(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255)

    siae = models.ForeignKey("siaes.Siae", verbose_name="Structure", related_name="labels", on_delete=models.CASCADE)

    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Label & certification"
        verbose_name_plural = "Labels & certifications"
        # ordering = ["id"]

    def __str__(self):
        return self.name


class SiaeClientReference(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=255, blank=True, null=True)
    description = models.TextField(verbose_name="Description", blank=True)
    image_name = models.CharField(verbose_name="Nom de l'image", max_length=255)
    order = models.PositiveIntegerField(verbose_name="Ordre", blank=False, default=1)

    siae = models.ForeignKey(
        "siaes.Siae", verbose_name="Structure", related_name="client_references", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField("Date de création", default=timezone.now)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)

    class Meta:
        verbose_name = "Référence client"
        verbose_name_plural = "Références clients"

    def __str__(self):
        return self.name
