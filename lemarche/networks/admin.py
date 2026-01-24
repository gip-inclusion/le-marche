from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from lemarche.networks.models import Network
from lemarche.utils.admin.admin_site import admin_site


@admin.register(Network, site=admin_site)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "brand", "siae_count_annotated_with_link", "created_at"]
    search_fields = ["id", "name", "brand"]
    search_help_text = "Cherche sur les champs : ID, Nom, Enseigne"

    readonly_fields = [
        "logo_url_display",
        "siae_count_annotated_with_link",
        "user_partner_count_annotated_with_link",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "brand", "website"),
            },
        ),
        ("Logo", {"fields": ("logo_url", "logo_url_display")}),
        ("Structures", {"fields": ("siae_count_annotated_with_link",)}),
        ("Utilisateurs (partenaires)", {"fields": ("user_partner_count_annotated_with_link",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        qs = qs.with_user_partner_stats()
        return qs

    def get_readonly_fields(self, request, obj=None):
        # slug cannot be changed (to avoid query errors)
        if obj:
            return self.readonly_fields + ["slug"]
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        # set slug on create
        if not obj:
            return {"slug": ("name",)}
        return {}

    def logo_url_display(self, instance):
        if instance.logo_url:
            return mark_safe(
                f'<a href="{instance.logo_url}" target="_blank">'
                f'<img src="{instance.logo_url}" title="{instance.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"

    def siae_count_annotated_with_link(self, network):
        url = reverse("admin:siaes_siae_changelist") + f"?networks__id__exact={network.id}"
        return format_html('<a href="{}">{}</a>', url, network.siae_count_annotated)

    siae_count_annotated_with_link.short_description = "Nombre de structures rattachées"
    siae_count_annotated_with_link.admin_order_field = "siae_count_annotated"

    def user_partner_count_annotated_with_link(self, network):
        url = reverse("admin:users_user_changelist") + f"?partner_network__id__exact={network.id}"
        return format_html('<a href="{}">{}</a>', url, network.user_partner_count_annotated)

    user_partner_count_annotated_with_link.short_description = "Nombre d'utilisateurs (partenaires) rattachés"
    user_partner_count_annotated_with_link.admin_order_field = "user_partner_count_annotated"
