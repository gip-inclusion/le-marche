from django.contrib import admin

from lemarche.tenders.models import Tender


# Register your models here.
@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "kind",
        "deadline_date",
        "response_kind",
        "start_working_date",
        "created_at",
    ]
    list_filter = ["kind", "deadline_date", "response_kind", "start_working_date"]
    # filter on "perimeters"? (loads ALL the perimeters... Use django-admin-autocomplete-filter instead?)
    search_fields = ["id", "title"]
    search_help_text = "Cherche sur les champs : ID, Titre"
