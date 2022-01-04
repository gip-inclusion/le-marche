from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from fieldsets_with_inlines import FieldsetsInlineMixin

from lemarche.siaes.models import Siae, SiaeClientReference, SiaeImage, SiaeLabel, SiaeOffer, SiaeUser
from lemarche.utils.fields import pretty_print_readonly_jsonfield


class IsLiveFilter(admin.SimpleListFilter):
    """Custom admin filter to target siaes who are live (active and not delisted)."""

    title = "Live ? (active et non délistée)"
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
    autocomplete_fields = ["user"]
    readonly_fields = ["created_at", "updated_at"]
    extra = 0


@admin.register(Siae)
class SiaeAdmin(FieldsetsInlineMixin, gis_admin.OSMGeoAdmin):
    list_display = [
        "id",
        "name",
        "siret",
        "kind",
        "city",
        "nb_users",
        "nb_offers",
        "nb_labels",
        "nb_cient_references",
        "nb_images",
        "created_at",
    ]
    list_filter = [IsLiveFilter, "is_first_page", HasUserFilter, "kind", "networks", "sectors", "geo_range"]
    search_fields = ["id", "name", "slug", "siret"]

    autocomplete_fields = ["sectors", "networks"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = [field for field in Siae.READONLY_FIELDS if field not in ("coords")] + [
        "sector_count",
        "network_count",
        "nb_offers",
        "nb_labels",
        "nb_cient_references",
        "nb_users",
        "nb_images",
        "coords_display",
        "logo_url",
        "logo_url_display",
        # "import_raw_object",
        "import_raw_object_display",
        "created_at",
        "updated_at",
    ]

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
            "Données C1 (ou ESAT)",
            {
                "fields": (
                    "name",
                    "slug",
                    "brand",
                    "siret",
                    "naf",
                    "kind",
                    "c1_id",
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
        ("Données API Entreprise", {"fields": Siae.READONLY_FIELDS_FROM_API_ENTREPRISE}),
        ("Quartiers de la politique de la ville (QPV)", {"fields": Siae.READONLY_FIELDS_FROM_QPV}),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "sectors",
                    "sector_count",
                    "networks",
                    "network_count",
                    "nb_offers",
                    "nb_labels",
                    "nb_cient_references",
                    "nb_images",
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
                    "nb_users",
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
        ("Si importé", {"fields": ("import_raw_object_display",)}),
        ("Autres", {"fields": ("created_at", "updated_at")}),
    ]

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     qs = qs.annotate(image_count=Count("images", distinct=True))
    #     return qs

    def nb_users(self, siae):
        # url = reverse("admin:users_user_changelist") + f"?siae__id__exact={siae.id}"
        # return format_html(f'<a href="{url}">{siae.user_count}</a>')
        return siae.user_count

    nb_users.short_description = "Nombre d'utilisateurs"
    nb_users.admin_order_field = "user_count"

    def nb_offers(self, siae):
        url = reverse("admin:siaes_siaeoffer_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.offer_count}</a>')

    nb_offers.short_description = "Nombre de prestations"
    nb_offers.admin_order_field = "offer_count"

    def nb_labels(self, siae):
        url = reverse("admin:siaes_siaelabel_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.label_count}</a>')

    nb_labels.short_description = "Nombre de labels"
    nb_labels.admin_order_field = "label_count"

    def nb_cient_references(self, siae):
        url = reverse("admin:siaes_siaeclientreference_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.client_reference_count}</a>')

    nb_cient_references.short_description = "Nombre de réf. clients"
    nb_cient_references.admin_order_field = "client_reference_count"

    def nb_images(self, siae):
        url = reverse("admin:siaes_siaeimage_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.image_count}</a>')

    nb_images.short_description = "Nombre d'images"
    nb_images.admin_order_field = "image_count"

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

    def import_raw_object_display(self, siae=None):
        if siae:
            return pretty_print_readonly_jsonfield(siae.import_raw_object)
        return "-"

    import_raw_object_display.short_description = "Donnée brute importée"


@admin.register(SiaeOffer)
class SiaeOfferAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "source", "created_at"]
    list_filter = ["source"]
    search_fields = ["id", "name", "siae__id", "siae__name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["source", "created_at", "updated_at"]

    def siae_with_link(self, instance):
        url = reverse("admin:siaes_siae_change", args=[instance.siae_id])
        return format_html(f'<a href="{url}">{instance.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeLabel)
class SiaeLabelAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["created_at", "updated_at"]

    def siae_with_link(self, instance):
        url = reverse("admin:siaes_siae_change", args=[instance.siae_id])
        return format_html(f'<a href="{url}">{instance.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeClientReference)
class SiaeClientReferenceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "logo_url", "logo_url_display", "created_at", "updated_at"]

    def siae_with_link(self, instance):
        url = reverse("admin:siaes_siae_change", args=[instance.siae_id])
        return format_html(f'<a href="{url}">{instance.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"

    def logo_url_display(self, instance):
        if instance.logo_url:
            return mark_safe(
                f'<a href="{instance.logo_url}" target="_blank">'
                f'<img src="{instance.logo_url}" title="{instance.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"


@admin.register(SiaeImage)
class SiaeImageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "image_url", "image_url_display", "created_at", "updated_at"]

    def siae_with_link(self, instance):
        url = reverse("admin:siaes_siae_change", args=[instance.siae_id])
        return format_html(f'<a href="{url}">{instance.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"

    def image_url_display(self, instance):
        if instance.image_url:
            return mark_safe(
                f'<a href="{instance.image_url}" target="_blank">'
                f'<img src="{instance.image_url}" title="{instance.image_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    image_url_display.short_description = "Image"
