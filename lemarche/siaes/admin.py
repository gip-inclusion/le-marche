from django import forms
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from fieldsets_with_inlines import FieldsetsInlineMixin

from lemarche.siaes.models import (
    Siae,
    SiaeClientReference,
    SiaeGroup,
    SiaeImage,
    SiaeLabel,
    SiaeOffer,
    SiaeUser,
    SiaeUserRequest,
)
from lemarche.users.models import User
from lemarche.utils.admin.actions import export_as_xls
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import ChoiceArrayField, pretty_print_readonly_jsonfield


class IsLiveFilter(admin.SimpleListFilter):
    """Custom admin filter to target siaes who are live (active and not delisted)."""

    title = "Live ? (active et non masquée)"
    parameter_name = "is_live"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.is_live()
        elif value == "No":
            return queryset.is_not_live()
        return queryset


class HasUserFilter(admin.SimpleListFilter):
    """Custom admin filter to target siaes who have at least 1 user."""

    title = "Avec un gestionnaire ?"
    parameter_name = "has_user"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_user()
        elif value == "No":
            return queryset.filter(users__isnull=True)
        return queryset


class SiaeUserInline(admin.TabularInline):
    model = SiaeUser
    fields = ["user", "user_with_link", "created_at", "updated_at"]
    autocomplete_fields = ["user"]
    readonly_fields = ["user_with_link", "created_at", "updated_at"]
    extra = 0

    def user_with_link(self, siae_user):
        url = reverse("admin:users_user_change", args=[siae_user.user_id])
        return format_html(f'<a href="{url}">{siae_user.user}</a>')

    user_with_link.short_description = User._meta.verbose_name


@admin.register(Siae, site=admin_site)
class SiaeAdmin(FieldsetsInlineMixin, gis_admin.OSMGeoAdmin):
    actions = [export_as_xls]
    list_display = [
        "id",
        "name",
        "siret",
        "kind",
        "city",
        "user_count_with_link",
        "offer_count_with_link",
        "label_count_with_link",
        "client_reference_count_with_link",
        "image_count_with_link",
        "tender_email_send_count_with_link",
        "tender_detail_display_count_with_link",
        "tender_detail_contact_click_count_with_link",
        "created_at",
    ]
    list_filter = [
        IsLiveFilter,
        "is_delisted",
        "is_first_page",
        HasUserFilter,
        "kind",
        "geo_range",
        "source",
        "networks",
        "sectors",
    ]
    search_fields = ["id", "name", "slug", "siret"]
    search_help_text = "Cherche sur les champs : ID, Raison sociale, Slug, Siret"

    autocomplete_fields = ["sectors", "networks", "groups"]
    # prepopulated_fields = {"slug": ("name",)}
    readonly_fields = [field for field in Siae.READONLY_FIELDS if field not in ("coords")] + [
        "sector_count_with_link",
        "network_count_with_link",
        "offer_count_with_link",
        "label_count_with_link",
        "client_reference_count_with_link",
        "user_count_with_link",
        "image_count_with_link",
        "coords_display",
        "logo_url",
        "logo_url_display",
        "tender_count_with_link",
        "tender_email_send_count_with_link",
        "tender_email_link_click_count_with_link",
        "tender_detail_display_count_with_link",
        "tender_detail_contact_click_count_with_link",
        "signup_date",
        "content_filled_basic_date",
        # "import_raw_object",
        "import_raw_object_display",
        "created_at",
        "updated_at",
    ]
    formfield_overrides = {
        ChoiceArrayField: {"widget": forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox-select-multiple"})},
    }

    # OSMGeoAdmin param for coords fields
    modifiable = False

    fieldsets_with_inlines = [
        (
            "Affichage",
            {
                "fields": ("is_active", "is_delisted", "is_first_page"),
            },
        ),
        (
            "Données C1 (ou ESAT ou SEP)",
            {
                "fields": (
                    "name",
                    "slug",
                    "brand",
                    "siret",
                    "naf",
                    "kind",
                    "nature",
                    "presta_type",
                    "c1_id",
                    "asp_id",
                    "website",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "post_code",
                    "department",
                    "region",
                    "coords_display",
                    "coords",
                    "source",
                )
            },
        ),
        ("Données C2", {"fields": Siae.READONLY_FIELDS_FROM_C2}),
        ("Données API Entreprise", {"fields": Siae.READONLY_FIELDS_FROM_API_ENTREPRISE}),
        (
            "Données API QPV (Quartier prioritaire de la politique de la ville)",
            {"fields": Siae.READONLY_FIELDS_FROM_QPV},
        ),
        ("Données API ZRR (Zone de revitalisation rurale)", {"fields": Siae.READONLY_FIELDS_FROM_ZRR}),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "sectors",
                    "sector_count_with_link",
                    "networks",
                    "network_count_with_link",
                    "offer_count_with_link",
                    "label_count_with_link",
                    "client_reference_count_with_link",
                    "image_count_with_link",
                    "groups",
                )
            },
        ),
        (
            "Périmètre d'intervention",
            {
                "fields": (
                    "geo_range",
                    "geo_range_custom_distance",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_first_name",
                    "contact_last_name",
                    "contact_email",
                    "contact_phone",
                    "contact_website",
                    "contact_social_website",
                    "user_count_with_link",
                )
            },
        ),
        SiaeUserInline,
        (
            "Logo",
            {
                "fields": (
                    "logo_url",
                    "logo_url_display",
                )
            },
        ),
        (
            "Besoins des acheteurs",
            {
                "fields": (
                    "tender_count_with_link",
                    "tender_email_send_count_with_link",
                    "tender_email_link_click_count_with_link",
                    "tender_detail_display_count_with_link",
                    "tender_detail_contact_click_count_with_link",
                )
            },
        ),
        (
            "Stats",
            {
                "fields": (
                    "signup_date",
                    "content_filled_basic_date",
                )
            },
        ),
        ("Si importé", {"fields": ("import_raw_object_display",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    ]

    add_fieldsets = [
        # (
        #     "Affichage",
        #     {
        #         "fields": (
        #             "is_active",
        #             # "is_delisted",
        #             # "is_first_page"
        #         ),
        #     },
        # ),
        (
            "Données C1 (ou ESAT ou SEP)",
            {
                "fields": (
                    "name",
                    "slug",
                    "brand",
                    "siret",
                    "naf",
                    "kind",
                    "nature",
                    "presta_type",
                    # "c1_id",
                    # "asp_id",
                    "website",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "post_code",
                    "department",
                    "region",
                    # "coords_display",
                    # "coords",
                    "source",
                )
            },
        ),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "sectors",
                    "networks",
                    # "groups",
                )
            },
        ),
        (
            "Périmètre d'intervention",
            {
                "fields": (
                    "geo_range",
                    "geo_range_custom_distance",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_first_name",
                    "contact_last_name",
                    "contact_email",
                    "contact_phone",
                    "contact_website",
                    "contact_social_website",
                )
            },
        ),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_tender_stats()
        return qs

    def get_readonly_fields(self, request, obj=None):
        """
        Staff can create and edit some Siaes.
        The editable fields are listed in add_fieldsets.
        """
        add_fields = []
        for fieldset in self.add_fieldsets:
            add_fields.extend(list(fieldset[1]["fields"]))
        add_readonly_fields = [field for field in self.readonly_fields if field not in add_fields] + ["slug", "source"]
        # add form
        if not obj:
            return add_readonly_fields
        # also allow edition of some specific Siae
        if obj and obj.source in [Siae.SOURCE_STAFF_C4_CREATED, Siae.SOURCE_ESAT]:
            return add_readonly_fields + ["name"]
        # for the rest, use the default full-version list
        return self.readonly_fields

    def get_fieldsets(self, request, obj=None):
        """
        The add form has a lighter fieldsets.
        (add_fieldsets is only available for User Admin, so we need to set it manually)
        """
        if not obj:
            self.fieldsets_with_inlines = self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_changeform_initial_data(self, request):
        """
        Default values in add form.
        """
        return {"is_active": False, "source": Siae.SOURCE_STAFF_C4_CREATED}

    def lookup_allowed(self, lookup, *args, **kwargs):
        if lookup in [
            "tendersiae__email_send_date__isnull",
            "tendersiae__email_link_click_date__isnull",
            "tendersiae__detail_display_date__isnull",
            "tendersiae__detail_contact_click_date__isnull",
        ]:
            return True
        return super().lookup_allowed(lookup, *args, **kwargs)

    def user_count_with_link(self, siae):
        url = reverse("admin:users_user_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.user_count}</a>')

    user_count_with_link.short_description = "Nombre d'utilisateurs"
    user_count_with_link.admin_order_field = "user_count"

    def sector_count_with_link(self, siae):
        url = reverse("admin:sectors_sector_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.sector_count}</a>')

    sector_count_with_link.short_description = "Nbr de secteurs"
    sector_count_with_link.admin_order_field = "sector_count"

    def network_count_with_link(self, siae):
        url = reverse("admin:networks_network_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.network_count}</a>')

    network_count_with_link.short_description = "Nbr de réseaux"
    network_count_with_link.admin_order_field = "network_count"

    def offer_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeoffer_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.offer_count}</a>')

    offer_count_with_link.short_description = "Nbr de prestations"
    offer_count_with_link.admin_order_field = "offer_count"

    def label_count_with_link(self, siae):
        url = reverse("admin:siaes_siaelabel_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.label_count}</a>')

    label_count_with_link.short_description = "Nbr de labels"
    label_count_with_link.admin_order_field = "label_count"

    def client_reference_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeclientreference_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.client_reference_count}</a>')

    client_reference_count_with_link.short_description = "Nbr de réf. clients"
    client_reference_count_with_link.admin_order_field = "client_reference_count"

    def image_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeimage_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.image_count}</a>')

    image_count_with_link.short_description = "Nbr d'images"
    image_count_with_link.admin_order_field = "image_count"

    def coords_display(self, siae):
        if siae.coords:
            return f"{siae.latitude} / {siae.longitude}"
        return "-"

    coords_display.short_description = "Coords (LAT / LNG)"

    def logo_url_display(self, siae):
        if siae.logo_url:
            return mark_safe(
                f'<a href="{siae.logo_url}" target="_blank">'
                f'<img src="{siae.logo_url}" title="{siae.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"

    def import_raw_object_display(self, instance: Siae = None):
        if instance:
            return pretty_print_readonly_jsonfield(instance.import_raw_object)
        return "-"

    import_raw_object_display.short_description = Siae._meta.get_field("import_raw_object").verbose_name

    def tender_count_with_link(self, siae):
        url = reverse("admin:tenders_tender_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{getattr(siae, "tender_count", 0)}</a>')

    tender_count_with_link.short_description = "Besoins concernés"
    tender_count_with_link.admin_order_field = "tender_count"

    def tender_email_send_count_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__email_send_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_email_send_count", 0)}</a>')

    tender_email_send_count_with_link.short_description = "Besoins reçus"
    tender_email_send_count_with_link.admin_order_field = "tender_email_send_count"

    def tender_email_link_click_count_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__email_link_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_email_link_click_count", 0)}</a>')

    tender_email_link_click_count_with_link.short_description = "Besoins cliqués"
    tender_email_link_click_count_with_link.admin_order_field = "tender_email_link_click_count"

    def tender_detail_display_count_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__detail_display_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_detail_display_count", 0)}</a>')

    tender_detail_display_count_with_link.short_description = "Besoins vues"
    tender_detail_display_count_with_link.admin_order_field = "tender_detail_display_count"

    def tender_detail_contact_click_count_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__detail_contact_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_detail_contact_click_count", 0)}</a>')

    tender_detail_contact_click_count_with_link.short_description = "Besoins intéressés"
    tender_detail_contact_click_count_with_link.admin_order_field = "tender_detail_contact_click_count"


@admin.register(SiaeUserRequest, site=admin_site)
class SiaeUserRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "siae", "initiator", "assignee", "response", "created_at", "updated_at"]
    search_fields = [
        "id",
        "siae__id",
        "siae__name",
        "initiator__id",
        "initiator__email",
        "assignee__id",
        "assignee__email",
    ]
    search_help_text = (
        "Cherche sur les champs : ID, Structure (ID, Nom), Initiateur (ID, E-mail), Responsable (ID, E-mail)"
    )

    autocomplete_fields = ["siae"]
    readonly_fields = [field.name for field in SiaeUserRequest._meta.fields]
    fields = ["logs_display" if field_name == "logs" else field_name for field_name in readonly_fields]

    def logs_display(self, siaeuserrequest=None):
        if siaeuserrequest:
            return pretty_print_readonly_jsonfield(siaeuserrequest.logs)
        return "-"

    logs_display.short_description = SiaeUserRequest._meta.get_field("logs").verbose_name

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiaeOffer, site=admin_site)
class SiaeOfferAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "source", "created_at"]
    list_filter = ["source"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["source", "created_at", "updated_at"]

    def siae_with_link(self, siae_offer):
        url = reverse("admin:siaes_siae_change", args=[siae_offer.siae_id])
        return format_html(f'<a href="{url}">{siae_offer.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeLabel, site=admin_site)
class SiaeLabelAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["created_at", "updated_at"]

    def siae_with_link(self, siae_label):
        url = reverse("admin:siaes_siae_change", args=[siae_label.siae_id])
        return format_html(f'<a href="{url}">{siae_label.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeClientReference, site=admin_site)
class SiaeClientReferenceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "logo_url", "logo_url_display", "created_at", "updated_at"]

    def siae_with_link(self, siae_client_reference):
        url = reverse("admin:siaes_siae_change", args=[siae_client_reference.siae_id])
        return format_html(f'<a href="{url}">{siae_client_reference.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"

    def logo_url_display(self, siae_client_reference):
        if siae_client_reference.logo_url:
            return mark_safe(
                f'<a href="{siae_client_reference.logo_url}" target="_blank">'
                f'<img src="{siae_client_reference.logo_url}" title="{siae_client_reference.logo_url}" style="max-height:300px" />'  # noqa
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"


@admin.register(SiaeImage, site=admin_site)
class SiaeImageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "image_url", "image_url_display", "created_at", "updated_at"]

    def siae_with_link(self, siae_image):
        url = reverse("admin:siaes_siae_change", args=[siae_image.siae_id])
        return format_html(f'<a href="{url}">{siae_image.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"

    def image_url_display(self, siae_image):
        if siae_image.image_url:
            return mark_safe(
                f'<a href="{siae_image.image_url}" target="_blank">'
                f'<img src="{siae_image.image_url}" title="{siae_image.image_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    image_url_display.short_description = "Image"


@admin.register(SiaeGroup, site=admin_site)
class SiaeGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "nb_siaes", "created_at"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["sectors"]
    readonly_fields = [f"{field}_last_updated" for field in SiaeGroup.TRACK_UPDATE_FIELDS] + [
        "nb_siaes",
        "logo_url_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "siret"),
            },
        ),
        (
            "Détails",
            {
                "fields": (
                    "sectors",
                    "year_constitution",
                    "siae_count",
                    "siae_count_last_updated",
                    "nb_siaes",
                    "employees_insertion_count",
                    "employees_insertion_count_last_updated",
                    "employees_permanent_count",
                    "employees_permanent_count_last_updated",
                    "ca",
                    "ca_last_updated",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_first_name",
                    "contact_last_name",
                    "contact_email",
                    "contact_phone",
                    "contact_website",
                    "contact_social_website",
                )
            },
        ),
        (
            "Logo",
            {
                "fields": (
                    "logo_url",
                    "logo_url_display",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count_live=Count("siaes", distinct=True))
        return qs

    def nb_siaes(self, siae_group):
        url = reverse("admin:siaes_siae_changelist") + f"?groups__in={siae_group.id}"
        return format_html(f'<a href="{url}">{siae_group.siae_count_live}</a>')

    nb_siaes.short_description = "Nombre de structures (live)"
    nb_siaes.admin_order_field = "siae_count_live"

    def logo_url_display(self, siae_group):
        if siae_group.logo_url:
            return mark_safe(
                f'<a href="{siae_group.logo_url}" target="_blank">'
                f'<img src="{siae_group.logo_url}" title="{siae_group.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"
