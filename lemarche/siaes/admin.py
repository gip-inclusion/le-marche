from django.contrib import admin

from lemarche.siaes.models import SiaeNetwork, Siae


@admin.register(SiaeNetwork)
class SiaeNetworkAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "brand", "created_at"]
    search_fields = ["id", "name", "brand"]

    readonly_fields = ["created_at", "updated_at"]


@admin.register(Siae)
class SiaeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siret", "kind", "createdat"]
    list_filter = ["kind", "networks"]
    search_fields = ["id", "name"]

    readonly_fields = Siae.READONLY_FIELDS + ["createdat", "updatedat"]

    fieldsets = [
        ("Affichage", {
            "fields": (
                "is_active",
                "is_delisted",
                "is_first_page"
            ),
        }),
        ("Données C1", {
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
        }),
        ("Quartiers de la politique de la ville (QPV)", {
            "fields": Siae.READONLY_FIELDS_FROM_QPV
        }),
        ("Données APIGouv", {
            "fields": Siae.READONLY_FIELDS_FROM_APIGOUV
        }),
        ("Autres", {
            "fields": (
                "description",
            )
        })
    ]
