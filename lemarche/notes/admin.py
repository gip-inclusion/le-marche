from django.contrib import admin

from lemarche.notes.models import Note
from lemarche.utils.admin.admin_site import admin_site


@admin.register(Note, site=admin_site)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "created_at"]
    search_fields = ["id", "text"]
    search_help_text = "Cherche sur les champs : ID, Contenu"
