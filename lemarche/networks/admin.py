from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from lemarche.common.admin import admin_site
from lemarche.networks.models import Network


@admin.register(Network, site=admin_site)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "brand", "nb_siaes", "created_at"]
    search_fields = ["id", "name", "brand"]
    search_help_text = "Cherche sur les champs : ID, Nom, Enseigne"

    readonly_fields = ["nb_siaes", "created_at", "updated_at"]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "brand", "website"),
            },
        ),
        ("Structures", {"fields": ("nb_siaes",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count=Count("siaes", distinct=True))
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

    def nb_siaes(self, network):
        url = reverse("admin:siaes_siae_changelist") + f"?networks__id__exact={network.id}"
        return format_html(f'<a href="{url}">{network.siae_count}</a>')

    nb_siaes.short_description = "Nombre de structures rattachées"
    nb_siaes.admin_order_field = "siae_count"
