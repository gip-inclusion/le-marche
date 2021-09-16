from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

from lemarche.users.models import User
from lemarche.users.forms import UserChangeForm, UserCreationForm


class SiaeAdminFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who are linked to a SIAE."""

    title = 'Gestionnaire de structure ?'
    parameter_name = 'is_siae_admin'

    def lookups(self, request, model_admin):
        return (('Yes', 'Oui'), ('No', 'Non'))

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            return queryset.siae_admins()
        elif value == 'No':
            return queryset.filter(siaes__isnull=True)
        return queryset


class ApiKeyFilter(admin.SimpleListFilter):
    """Custom admin filter to target users with API Keys."""

    title = 'Clé API ?'
    parameter_name = 'has_api_key'

    def lookups(self, request, model_admin):
        return (('Yes', 'Oui'), ('No', 'Non'))

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            return queryset.with_api_key()
        elif value == 'No':
            return queryset.filter(api_key__isnull=True)
        return queryset


class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = ["id", "first_name", "last_name", "kind", "last_login", "created_at"]
    list_filter = ["kind", SiaeAdminFilter, ApiKeyFilter, "is_staff"]
    search_fields = ["id", "email"]
    ordering = ["-created_at"]

    readonly_fields = [field.name for field in User._meta.fields if field.name.startswith("c4_")] + \
        ["siae_admin_list", "last_login", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": (
                "email",
                "password",
            )
        }),
        ("Contact", {
            "fields": (
                "first_name",
                "last_name",
                "kind",
                "phone",
            )
        }),
        ("Structures", {
            "fields": (
                "siae_admin_list",
            )
        }),
        ("API", {
            "fields": (
                "api_key",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "groups"
            )
        }),
        ("Données C4 Symphony", {
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
                "c4_accept_survey",
                "c4_accept_rgpd",
                "c4_offers_for_pro_sector",
                "c4_quote_promise"
            )
        }),
        ("Autres", {
            "fields": (
                "last_login",
                "created_at",
                "updated_at",
            )
        })
    )
    add_fieldsets = (
        (None, {
            "fields": (
                "email",
                "password1",
                "password2",
                "is_active",
            )
        }),
        ("Contact", {
            "fields": (
                "first_name",
                "last_name",
                "kind",
                "phone",
            )
        }),
        ("API", {
            "fields": (
                "api_key",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_staff",
                "groups"
            )
        })
    )

    def siae_admin_list(self, user):
        siaes = user.siaes.all()
        if not siaes:
            return 'Aucune'
        else:
            html = ''
            for siae in siaes:
                html += format_html(
                    '<a href="{obj_url}">{obj_name}</a></br>',
                    obj_url=reverse('admin:siaes_siae_change', args=[siae.id]),
                    obj_name=siae)
            return format_html(html)
    siae_admin_list.short_description = 'Gestionnaire de'


admin.site.register(User, UserAdmin)
