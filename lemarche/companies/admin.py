from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from lemarche.companies.models import Company
from lemarche.utils.admin.admin_site import admin_site


class HasUserFilter(admin.SimpleListFilter):
    title = "Avec des utilisateurs ?"
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


class HasEmailDomainFilter(admin.SimpleListFilter):
    title = "Avec des noms de domaine d'e-mails ?"
    parameter_name = "has_email_domain"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_email_domain()
        elif value == "No":
            return queryset.filter(email_domain_list=[])
        return queryset


@admin.register(Company, site=admin_site)
class CompanyAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ["id", "name", "nb_users", "created_at"]
    list_filter = [HasUserFilter, HasEmailDomainFilter]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    readonly_fields = ["logo_url_display", "nb_users", "created_at", "updated_at"]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "description", "siret", "website", "email_domain_list"),
            },
        ),
        ("Logo", {"fields": ("logo_url", "logo_url_display")}),
        ("Utilisateurs", {"fields": ("nb_users",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(user_count=Count("users", distinct=True))
        qs = qs.order_by("name")
        return qs

    def get_readonly_fields(self, request, obj=None):
        # slug cannot be changed (to avoid query errors)
        if obj:
            return self.readonly_fields + ["slug"]
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        # set slug on create
        if not obj:
            return {"slug": ("name",)}
        return {}

    def logo_url_display(self, instance):
        if instance.logo_url:
            return mark_safe(
                f'<a href="{instance.logo_url}" target="_blank">'
                f'<img src="{instance.logo_url}" title="{instance.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"

    def nb_users(self, company):
        url = reverse("admin:users_user_changelist") + f"?company__id__exact={company.id}"
        return format_html(f'<a href="{url}">{company.user_count}</a>')

    nb_users.short_description = "Nombre d'utilisateurs rattachés"
    nb_users.admin_order_field = "user_count"
