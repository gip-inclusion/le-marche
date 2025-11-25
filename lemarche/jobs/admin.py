from django.contrib import admin

from lemarche.utils.admin.admin_site import admin_site

from .models import Appellation, Rome


@admin.register(Rome, site=admin_site)
class RomeAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]
    search_help_text = "Cherche sur les champs : Code, Nom"

    readonly_fields = [field.name for field in Rome._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Appellation, site=admin_site)
class AppellationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "rome"]
    list_filter = ["rome", "sectors"]
    search_fields = ["code", "name"]
    search_help_text = "Cherche sur les champs : Code, Nom"
    filter_horizontal = ["sectors"]

    readonly_fields = [field.name for field in Appellation._meta.fields if field.name != "sectors"] + ["sectors"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
