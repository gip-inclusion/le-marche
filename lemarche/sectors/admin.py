from django.contrib import admin

from lemarche.sectors.models import SectorGroup, Sector


@admin.register(SectorGroup)
class SectorGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_at"]
    search_fields = ["id", "name"]

    readonly_fields = ["created_at", "updated_at"]


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "group", "created_at"]
    list_filter = ["group"]
    search_fields = ["id", "name"]

    readonly_fields = ["created_at", "updated_at"]
