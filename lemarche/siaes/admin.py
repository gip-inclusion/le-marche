from django.contrib import admin

from lemarche.siaes.models import Siae


@admin.register(Siae)
class SiaeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siret", "kind", "createdat"]
    list_filter = ["kind"]
    search_fields = ["id", "name"]

    readonly_fields = [
        "name", "brand", "siret", "naf",
        "city", "post_code", "department", "region",
        "createdat", "updatedat"]
