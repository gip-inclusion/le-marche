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
        return format_html('<a href="{}">{}</a>', url, sector_group.sector_count_annotated)

    sector_count_annotated_with_link.short_description = "Secteurs d'activité"
    sector_count_annotated_with_link.admin_order_field = "sector_count_annotated"


@admin.register(Sector, site=admin_site)
class SectorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "siae_count_annotated_with_link",
        "tender_count_annotated_with_link",
        "group",
        "created_at",
    ]
    list_filter = ["group"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        qs = qs.with_tender_stats()
        return qs

    def siae_count_annotated_with_link(self, sector):
        url = reverse("admin:siaes_siae_changelist") + f"?sectors__id__exact={sector.id}"
        return format_html('<a href="{}">{}</a>', url, sector.siae_count_annotated)

    siae_count_annotated_with_link.short_description = "Structures rattachées"
    siae_count_annotated_with_link.admin_order_field = "siae_count_annotated"

    def tender_count_annotated_with_link(self, sector):
        url = reverse("admin:tenders_tender_changelist") + f"?sectors__id__exact={sector.id}"
        return format_html('<a href="{}">{}</a>', url, sector.tender_count_annotated)

    tender_count_annotated_with_link.short_description = "Besoins concernés"
    tender_count_annotated_with_link.admin_order_field = "tender_count_annotated"
