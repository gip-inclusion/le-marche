from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from fieldsets_with_inlines import FieldsetsInlineMixin

from lemarche.common.admin import admin_site
from lemarche.favorites.models import FavoriteItem, FavoriteList


class FavoriteItemInline(admin.TabularInline):
    model = FavoriteItem
    autocomplete_fields = ["siae"]
    readonly_fields = ["created_at", "updated_at"]
    extra = 0


@admin.register(FavoriteList, site=admin_site)
class FavoriteListAdmin(FieldsetsInlineMixin, admin.ModelAdmin):
    list_display = ["id", "name", "user_with_link", "nb_siaes", "created_at", "updated_at"]
    search_fields = ["id", "name", "slug", "user__id", "user__email"]
    search_help_text = "Cherche sur les champs : ID, Nom, Slug, Utilisateur (ID, E-mail)"

    autocomplete_fields = ["user"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    fieldsets_with_inlines = [
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                )
            },
        ),
        ("Utilisateur", {"fields": ("user",)}),
        FavoriteItemInline,
        ("Dates", {"fields": ("created_at", "updated_at")}),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count=Count("siaes", distinct=True))
        return qs

    def user_with_link(self, favorite_list):
        url = reverse("admin:users_user_change", args=[favorite_list.user_id])
        return format_html(f'<a href="{url}">{favorite_list.user}</a>')

    user_with_link.short_description = "Utilisateur"
    user_with_link.admin_order_field = "user"

    def nb_siaes(self, favorite_list):
        url = reverse("admin:siaes_siae_changelist") + f"?favorite_lists__in={favorite_list.id}"
        return format_html(f'<a href="{url}">{favorite_list.siae_count}</a>')

    nb_siaes.short_description = "Nombre de structures"
    nb_siaes.admin_order_field = "siae_count"
