from django.contrib import admin

from lemarche.networks.models import Network


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "brand", "created_at"]
    search_fields = ["id", "name", "brand"]

    readonly_fields = ["created_at", "updated_at"]
