from django.contrib import admin

from lemarche.notes.models import Note
from lemarche.utils.admin.admin_site import admin_site


class HasTenderFilter(admin.SimpleListFilter):
    title = "Rattaché à un besoin ?"
    parameter_name = "has_tender"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_tender()
        elif value == "No":
            return queryset.filter(tenders__isnull=True)
        return queryset


@admin.register(Note, site=admin_site)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["id", "author", "text", "tender", "created_at"]
    list_filter = [HasTenderFilter]
    search_fields = ["id", "text"]
    search_help_text = "Cherche sur les champs : ID, Contenu"

    readonly_fields = [
        "author",
        "tender",
        "created_at",
        "updated_at",
    ]

    def save_model(self, request, obj: Note, form, change):
        """
        Set Note author on create
        """
        if not obj.id and not obj.author_id:
            obj.author = request.user
        obj.save()
