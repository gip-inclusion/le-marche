from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, mark_safe

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


class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = ["id", "first_name", "last_name", "kind", "nb_siaes", "last_login", "created_at"]
    list_filter = ["kind", HasSiaeFilter, HasFavoriteListFilter, HasApiKeyFilter, "is_staff"]
    search_fields = ["id", "email", "first_name", "last_name"]
    ordering = ["-created_at"]

    # autocomplete_fields = ["siaes"]
    readonly_fields = [field.name for field in User._meta.fields if field.name.startswith("c4_")] + [
        "nb_siaes",
        "user_siae_admin_list",
        "user_favorite_list",
        "last_login",
        "image_url",
        "image_url_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
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
        (
            "Structures",
            {
                "description": "Ajouter l'utilisateur à une nouvelle structure ? Possible en se rendant sur la fiche de la structure.",  # noqa
                "fields": ("user_siae_admin_list",),
            },
        ),
        (
            "Listes d'achats favoris",
            {
                "fields": ("user_favorite_list",),
            },
        ),
        (
            "RGPD & co",
            {
                "fields": (
                    "accept_rgpd",
                    "accept_survey",
                    "accept_offers_for_pro_sector",
                    "accept_quote_promise",
                )
            },
        ),
        ("API", {"fields": ("api_key",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "groups")}),
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
        (
            "Autres",
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
        ("Permissions", {"fields": ("is_staff", "groups")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count=Count("siaes", distinct=True))
        return qs

    def nb_siaes(self, user):
        if user.siae_count:
            url = reverse("admin:siaes_siae_changelist") + f"?users__in={user.id}"
            return format_html(f'<a href="{url}">{user.siae_count}</a>')
        return "-"

    nb_siaes.short_description = "Nombre de structures"
    nb_siaes.admin_order_field = "siae_count"

    def user_siae_admin_list(self, user):
        siaes = user.siaes.all()
        if not siaes:
            return "Aucune"
        else:
            html = ""
            for siae in siaes:
                html += format_html(
                    '<a href="{obj_url}">{obj_name}</a></br>',
                    obj_url=reverse("admin:siaes_siae_change", args=[siae.id]),
                    obj_name=siae,
                )
            return format_html(html)

    user_siae_admin_list.short_description = "Gestionnaire de"

    def user_favorite_list(self, user):
        favorite_lists = user.favorite_lists.all()
        if not favorite_lists:
            return "Aucune"
        else:
            html = ""
            for favorite_list in favorite_lists:
                html += format_html(
                    '<a href="{obj_url}">{obj_name}</a></br>',
                    obj_url=reverse("admin:favorites_favoritelist_change", args=[favorite_list.id]),
                    obj_name=favorite_list,
                )
            return format_html(html)

    user_favorite_list.short_description = "Listes d'achats"

    def image_url_display(self, user):
        if user.image_url:
            return mark_safe(
                f'<a href="{user.image_url}" target="_blank">'
                f'<img src="{user.image_url}" title="{user.image_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    image_url_display.short_description = "Image"


admin.site.register(User, UserAdmin)
