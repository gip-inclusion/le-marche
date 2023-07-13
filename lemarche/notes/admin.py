from django.contrib import admin

from lemarche.notes.models import Note
from lemarche.utils.admin.admin_site import admin_site


@admin.register(Note, site=admin_site)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["id", "author", "text", "tender", "created_at"]
    search_fields = ["id", "text"]
    search_help_text = "Cherche sur les champs : ID, Contenu"

    readonly_fields = [
        "author",
        "tender",
        "created_at",
        "updated_at",
    ]

    def save_model(self, request, obj: Note, form, change):
        if not obj.id and not obj.author_id:
            obj.author = request.user
        obj.save()
