from django.contrib import admin

from lemarche.common.admin import admin_site
from lemarche.networks.models import Network


@admin.register(Network, site=admin_site)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "brand", "created_at"]
    search_fields = ["id", "name", "brand"]
    search_help_text = "Cherche sur les champs : ID, Nom, Enseigne"

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
