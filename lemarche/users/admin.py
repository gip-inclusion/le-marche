from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from fieldsets_with_inlines import FieldsetsInlineMixin

from lemarche.common.admin import admin_site
from lemarche.siaes.models import Siae, SiaeUser
from lemarche.users.forms import UserChangeForm, UserCreationForm
from lemarche.users.models import User


class HasSiaeFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who are linked to a Siae."""

    title = "Gestionnaire de structure ?"
    parameter_name = "has_siae"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_siae()
        elif value == "No":
            return queryset.filter(siaes__isnull=True)
        return queryset


class HasTenderFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who have tenders."""

    title = "Besoin déposé ?"
    parameter_name = "has_tender"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_tender()
        elif value == "No":
            return queryset.filter(tenders__isnull=True)
        return queryset


class HasFavoriteListFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who have favorite lists."""

    title = "Listes d'achats favoris ?"
    parameter_name = "has_favorite_list"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_favorite_list()
        elif value == "No":
            return queryset.filter(favorite_lists__isnull=True)
        return queryset


class HasApiKeyFilter(admin.SimpleListFilter):
    """Custom admin filter to target users with API Keys."""

    title = "Clé API ?"
    parameter_name = "has_api_key"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.with_api_key()
        elif value == "No":
            return queryset.filter(api_key__isnull=True)
        return queryset


class SiaeUserInline(admin.TabularInline):
    model = SiaeUser
    fields = ["siae", "siae_with_link", "created_at", "updated_at"]
    autocomplete_fields = ["siae"]
    readonly_fields = ["siae_with_link", "created_at", "updated_at"]
    extra = 0

    def siae_with_link(self, siae_user):
        url = reverse("admin:siaes_siae_change", args=[siae_user.siae_id])
        return format_html(f'<a href="{url}">{siae_user.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name


@admin.register(User, site=admin_site)
class UserAdmin(FieldsetsInlineMixin, UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = [
        "id",
        "first_name",
        "last_name",
        "kind",
        "siae_count_with_link",
        "tender_count_with_link",
        "last_login",
        "created_at",
    ]
    list_filter = [
        "kind",
        HasSiaeFilter,
        HasTenderFilter,
        "partner_kind",
        HasFavoriteListFilter,
        HasApiKeyFilter,
        "is_staff",
        "is_superuser",
    ]
    search_fields = ["id", "email", "first_name", "last_name"]
    search_help_text = "Cherche sur les champs : ID, E-mail, Prénom, Nom"
    ordering = ["-created_at"]

    # autocomplete_fields = ["siaes"]
    readonly_fields = (
        [field.name for field in User._meta.fields if field.name.startswith("c4_")]
        + [f"{field}_last_updated" for field in User.TRACK_UPDATE_FIELDS]
        + [field.name for field in User._meta.fields if field.name.endswith("_last_seen_date")]
        + [
            "siae_count_with_link",
            "tender_count_with_link",
            "favorite_list_count_with_link",
            "last_login",
            "image_url",
            "image_url_display",
            "created_at",
            "updated_at",
        ]
    )

    fieldsets_with_inlines = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "kind",
                    "phone",
                    "company_name",
                    "position",
                    "partner_kind",
                )
            },
        ),
        SiaeUserInline,
        (
            "Besoins déposés",
            {
                "fields": ("tender_count_with_link",),
            },
        ),
        (
            "Listes d'achats favoris",
            {
                "fields": ("favorite_list_count_with_link",),
            },
        ),
        (
            "RGPD & co",
            {
                "fields": (
                    "accept_rgpd",
                    "accept_survey",
                    "accept_share_contact_to_external_partners",
                    "source",
                )
            },
        ),
        ("API", {"fields": ("api_key", "api_key_last_updated")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        (
            "Données C4 Cocorico",
            {
                "fields": (
                    "c4_id",
                    "c4_website",
                    "c4_siret",
                    "c4_naf",
                    "c4_phone_prefix",
                    "c4_time_zone",
                    "c4_phone_verified",
                    "c4_email_verified",
                    "c4_id_card_verified",
                    "image_url",
                    "image_url_display",
                )
            },
        ),
        ("Stats", {"fields": ("dashboard_last_seen_date", "tender_list_last_seen_date")}),
        (
            "Dates",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "kind",
                    "phone",
                )
            },
        ),
        ("API", {"fields": ("api_key",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            siae_count=Count("siaes", distinct=True),
            tender_count=Count("tenders", distinct=True),
            favorite_list_count=Count("favorite_lists", distinct=True),
        )
        return qs

    def siae_count_with_link(self, user):
        if user.siae_count:
            url = reverse("admin:siaes_siae_changelist") + f"?users__in={user.id}"
            return format_html(f'<a href="{url}">{user.siae_count}</a>')
        return "-"

    siae_count_with_link.short_description = "Nombre de structures"
    siae_count_with_link.admin_order_field = "siae_count"

    def tender_count_with_link(self, user):
        if user.tender_count:
            url = reverse("admin:tenders_tender_changelist") + f"?users__in={user.id}"
            return format_html(f'<a href="{url}">{user.tender_count}</a>')
        return "-"

    tender_count_with_link.short_description = "Nombre de besoins"
    tender_count_with_link.admin_order_field = "tender_count"

    def favorite_list_count_with_link(self, user):
        if user.favorite_list_count:
            url = reverse("admin:favorites_favoritelist_changelist") + f"?users__in={user.id}"
            return format_html(f'<a href="{url}">{user.favorite_list_count}</a>')
        return "-"

    favorite_list_count_with_link.short_description = "Nombre de listes d'achats"
    favorite_list_count_with_link.admin_order_field = "favorite_list_count"

    def image_url_display(self, user):
        if user.image_url:
            return mark_safe(
                f'<a href="{user.image_url}" target="_blank">'
                f'<img src="{user.image_url}" title="{user.image_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    image_url_display.short_description = "Image"
