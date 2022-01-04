from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from fieldsets_with_inlines import FieldsetsInlineMixin

from lemarche.favorites.models import FavoriteItem, FavoriteList


class FavoriteItemInline(admin.TabularInline):
    model = FavoriteItem
    autocomplete_fields = ["siae"]
    readonly_fields = ["created_at", "updated_at"]
    extra = 0


@admin.register(FavoriteList)
class FavoriteListAdmin(FieldsetsInlineMixin, admin.ModelAdmin):
    list_display = ["id", "name", "user_with_link", "nb_siaes", "created_at", "updated_at"]
    search_fields = ["id", "name", "slug", "user__id", "user__email"]

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
        ("Autres", {"fields": ("created_at", "updated_at")}),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(siae_count=Count("siaes", distinct=True))
        return qs

    def user_with_link(self, instance):
        url = reverse("admin:users_user_change", args=[instance.user_id])
        return format_html(f'<a href="{url}">{instance.user}</a>')

    user_with_link.short_description = "Utilisateur"
    user_with_link.admin_order_field = "user"

    def nb_siaes(self, favorite_list):
        # url = reverse("admin:siaes_siae_changelist") + f"?favorite_list__id__exact={favorite_list.id}"
        # return format_html(f'<a href="{url}">{favorite_list.siae_count}</a>')
        return favorite_list.siae_count

    nb_siaes.short_description = "Nombre de structures"
    nb_siaes.admin_order_field = "siae_count"
