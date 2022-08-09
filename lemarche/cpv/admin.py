from django.contrib import admin

from lemarche.common.admin import admin_site
from lemarche.cpv.models import Code


@admin.register(Code, site=admin_site)
class CodeAdmin(admin.ModelAdmin):
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
