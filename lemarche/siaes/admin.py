from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from lemarche.siaes.models import Siae, SiaeOffer, SiaeLabel, SiaeClientReference


@admin.register(Siae)
class SiaeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siret", "kind", "nb_offers", "nb_labels", "nb_cient_references", "created_at"]
    list_filter = ["kind", "networks"]
    search_fields = ["id", "name"]

    autocomplete_fields = ["sectors", "networks", "users"]
    readonly_fields = Siae.READONLY_FIELDS + ["created_at", "updated_at"]

    fieldsets = [
        (
            "Affichage",
            {
                "fields": ("is_active", "is_delisted", "is_first_page"),
            },
        ),
        (
            "Données C1",
            {
                "fields": (
                    "name",
                    "brand",
                    "siret",
                    "naf",
                    "kind",
                    "c1_id",
                    "city",
                    "post_code",
                    "department",
                    "region",
                )
            },
        ),
        ("Quartiers de la politique de la ville (QPV)", {"fields": Siae.READONLY_FIELDS_FROM_QPV}),
        ("Données APIGouv", {"fields": Siae.READONLY_FIELDS_FROM_APIGOUV}),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "sectors",
                    "networks",
                    "users",
                )
            },
        ),
        ("Autres", {"fields": ("created_at", "updated_at")}),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = (
            qs.annotate(offer_count=Count("offers"))
            .annotate(label_count=Count("labels"))
            .annotate(client_reference_count=Count("client_references"))
        )
        return qs

    def nb_offers(self, siae):
        url = reverse("admin:siaes_siaeoffer_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.offer_count}</a>')

    nb_offers.short_description = "Nombre de prestations"
    nb_offers.admin_order_field = "offer_count"

    def nb_labels(self, siae):
        url = reverse("admin:siaes_siaeoffer_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.label_count}</a>')

    nb_labels.short_description = "Nombre de labels"
    nb_labels.admin_order_field = "label_count"

    def nb_cient_references(self, siae):
        url = reverse("admin:siaes_siaeoffer_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.client_reference_count}</a>')

    nb_cient_references.short_description = "Nombre de réf. clients"
    nb_cient_references.admin_order_field = "client_reference_count"


@admin.register(SiaeOffer)
class SiaeOfferAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "source", "created_at"]
    list_filter = ["source"]
    search_fields = ["id", "name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["source", "created_at", "updated_at"]

    def siae_with_link(self, offer):
        url = reverse("admin:siaes_siae_change", args=[offer.siae_id])
        return format_html(f'<a href="{url}">{offer.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeLabel)
class SiaeLabelAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["created_at", "updated_at"]

    def siae_with_link(self, label):
        url = reverse("admin:siaes_siae_change", args=[label.siae_id])
        return format_html(f'<a href="{url}">{label.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeClientReference)
class SiaeClientReferenceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name"]

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "created_at", "updated_at"]

    def siae_with_link(self, client_reference):
        url = reverse("admin:siaes_siae_change", args=[client_reference.siae_id])
        return format_html(f'<a href="{url}">{client_reference.siae}</a>')

    siae_with_link.short_description = "Structure"
    siae_with_link.admin_order_field = "siae"
