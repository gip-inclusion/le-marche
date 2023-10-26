from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from lemarche.sectors.models import Sector, SectorGroup
from lemarche.utils.admin.admin_site import admin_site


@admin.register(SectorGroup, site=admin_site)
class SectorGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "sector_count_annotated_with_link", "created_at"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_sector_stats()
        return qs

    def sector_count_annotated_with_link(self, sector_group):
        url = reverse("admin:sectors_sector_changelist") + f"?group__id__exact={sector_group.id}"
        return format_html(f'<a href="{url}">{sector_group.sector_count_annotated}</a>')

    sector_count_annotated_with_link.short_description = "Nombre de secteurs d'activité"
    sector_count_annotated_with_link.admin_order_field = "sector_count_annotated"


@admin.register(Sector, site=admin_site)
class SectorAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_count_annotated_with_link", "group", "created_at"]
    list_filter = ["group"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        return qs

    def siae_count_annotated_with_link(self, sector):
        url = reverse("admin:siaes_siae_changelist") + f"?sectors__id__exact={sector.id}"
        return format_html(f'<a href="{url}">{sector.siae_count_annotated}</a>')

    siae_count_annotated_with_link.short_description = "Nombre de structures rattachées"
    siae_count_annotated_with_link.admin_order_field = "siae_count_annotated"
