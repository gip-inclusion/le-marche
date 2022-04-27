from django.contrib import admin

from lemarche.common.admin import admin_site
from lemarche.perimeters.models import Perimeter


@admin.register(Perimeter, site=admin_site)
class PerimeterAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "kind", "insee_code", "post_codes", "department_code", "region_code", "created_at"]
    list_filter = ["kind", "region_code", "department_code"]
    search_fields = ["id", "name", "insee_code", "post_codes"]
    search_help_text = "Cherche sur les champs : ID, Nom, Code INSEE, Codes postaux"

    readonly_fields = [field.name for field in Perimeter._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
