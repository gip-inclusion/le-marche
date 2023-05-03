from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from lemarche.sectors.models import Sector, SectorGroup
from lemarche.utils.admin.admin_site import admin_site


@admin.register(SectorGroup, site=admin_site)
class SectorGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "nb_sectors", "created_at"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(sector_count=Count("sectors", distinct=True))
        return qs

    def nb_sectors(self, sector_group):
        url = reverse("admin:sectors_sector_changelist") + f"?group__id__exact={sector_group.id}"
        return format_html(f'<a href="{url}">{sector_group.sector_count}</a>')

    nb_sectors.short_description = "Nombre de secteurs d'activité"
    nb_sectors.admin_order_field = "sector_count"


@admin.register(Sector, site=admin_site)
class SectorAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "nb_siaes", "group", "created_at"]
    list_filter = ["group"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count=Count("siaes", distinct=True))
        return qs

    def nb_siaes(self, sector):
        url = reverse("admin:siaes_siae_changelist") + f"?sectors__id__exact={sector.id}"
        return format_html(f'<a href="{url}">{sector.siae_count}</a>')

    nb_siaes.short_description = "Nombre de structures rattachées"
    nb_siaes.admin_order_field = "siae_count"
