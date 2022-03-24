from django.contrib import admin

from lemarche.tenders.models import Tender


# Register your models here.
@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "author",
        "kind",
        "deadline_date",
        "start_working_date",
        "response_kind",
        "siae_found_count",
        "created_at",
    ]
    list_filter = ["kind", "deadline_date", "start_working_date", "response_kind"]
    # filter on "perimeters"? (loads ALL the perimeters... Use django-admin-autocomplete-filter instead?)
    search_fields = ["id", "title"]
    search_help_text = "Cherche sur les champs : ID, Titre"
    readonly_fields = ["siae_found_count"]

    autocomplete_fields = ["perimeters", "sectors"]
