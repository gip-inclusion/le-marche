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

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count=Count("siaes", distinct=True))
        return qs

    def nb_siaes(self, network):
        url = reverse("admin:siaes_siae_changelist") + f"?networks__id__exact={network.id}"
        return format_html(f'<a href="{url}">{network.siae_count}</a>')

    nb_siaes.short_description = "Nombre de structures rattachées"
    nb_siaes.admin_order_field = "siae_count"
