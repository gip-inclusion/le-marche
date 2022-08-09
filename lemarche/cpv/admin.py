from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from lemarche.common.admin import admin_site
from lemarche.cpv.models import Code


@admin.register(Code, site=admin_site)
class CodeAdmin(admin.ModelAdmin):
    list_display = ["cpv_code", "name", "nb_sectors", "created_at", "updated_at"]

    autocomplete_fields = ["sectors"]
    readonly_fields = ["name", "slug", "cpv_code", "created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "cpv_code",
                )
            },
        ),
        ("Secteurs d'activité (correspondance)", {"fields": ("sectors",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("sectors")
        qs = qs.annotate(sector_count=Count("sectors", distinct=True))
        return qs

    def nb_sectors(self, code):
        url = reverse("admin:sectors_sector_changelist") + f"?cpv_codes__in={code.id}"
        return format_html(f'<a href="{url}">{code.sector_count}</a>')

    nb_sectors.short_description = "Nombre de secteurs correspondants"
    nb_sectors.admin_order_field = "sector_count"
