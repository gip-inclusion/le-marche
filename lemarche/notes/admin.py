from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from lemarche.notes.models import Note
from lemarche.utils.admin.admin_site import admin_site


@admin.register(Note, site=admin_site)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["id", "author", "text", "content_type", "created_at"]
    search_fields = ["id", "text"]
    search_help_text = "Cherche sur les champs : ID, Contenu"

    readonly_fields = [
        "content_type",
        "object_id",
        "object_id_with_link",
        "author",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("text", "author"),
            },
        ),
        ("Rattachée à…", {"fields": ("content_type", "object_id_with_link")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj: Note, form, change):
        if not obj.id and not obj.author_id:
            obj.author = request.user
        obj.save()

    def object_id_with_link(self, note):
        if note.content_type and note.object_id:
            if note.content_type.model == "tender":
                url = reverse("admin:tenders_tender_change", args=[note.object_id])
                return format_html(f'<a href="{url}">{note.object_id}</a>')
            elif note.content_type.model == "siae":
                url = reverse("admin:siaes_siae_change", args=[note.object_id])
                return format_html(f'<a href="{url}">{note.object_id}</a>')
            elif note.content_type.model == "user":
                url = reverse("admin:users_user_change", args=[note.object_id])
                return format_html(f'<a href="{url}">{note.object_id}</a>')
        return note.object.id
