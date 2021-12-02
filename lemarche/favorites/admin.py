from django.contrib import admin

from lemarche.favorites.models import FavoriteList


@admin.register(FavoriteList)
class FavoriteListAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "user", "created_at"]
    search_fields = ["id", "name", "user__id"]

    autocomplete_fields = ["user"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
