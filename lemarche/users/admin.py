from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from lemarche.users.models import User
from lemarche.users.forms import UserChangeForm, UserCreationForm


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

    list_display = ["id", "first_name", "last_name", "company_name", "kind", "last_login", "created_at"]
    list_filter = ["kind", ApiKeyFilter, "is_staff"]
    search_fields = ["id", "email"]
    ordering = ["-created_at"]

    readonly_fields = ["c4_id", "last_login", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": (
                "email",
                "password",
                "api_key"
            )
        }),
        ("Contact", {
            "fields": (
                "first_name",
                "last_name",
                "kind",
            )
        }),
        ("Structure", {
            "fields": (
                "phone",
                "website",
                "company_name",
                "siret",
                "naf"
            )
        }),
        ("Permissions", {
            "fields": (
                "is_staff",
                "is_active",
                "groups"
            )
        }),
        ("Autres", {
            "fields": (
                "c4_id",
                "last_login",
                "created_at",
                "updated_at",
            )
        })
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "is_staff",
                "is_active",
                "api_key",
                "groups"
            )
        }),
    )


admin.site.register(User, UserAdmin)
