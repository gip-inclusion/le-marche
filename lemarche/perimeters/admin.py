from django.contrib import admin

from lemarche.perimeters.models import Perimeter


@admin.register(Perimeter)
class PerimeterAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "kind", "insee_code", "post_codes", "department_code", "region_code", "created_at"]
    list_filter = ["kind", "region_code", "department_code"]
    search_fields = ["id", "name", "insee_code", "post_codes"]

    readonly_fields = [field.name for field in Perimeter._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
