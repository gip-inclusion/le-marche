from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models

from ckeditor.widgets import CKEditorWidget

from lemarche.pages.models import Page


class PageAdmin(FlatPageAdmin):
    list_display = ["url", "title", "created_at", "updated_at"]

    readonly_fields = ["created_at", "updated_at"]
    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget}
    }

    fieldsets = (
        (None, {
            "fields": (
                "url",
                "title",
                "content"
            ),
        }),
        ("SEO", {
            "fields": (
                "meta_title",
                "meta_description"
            )
        }),
        ("Info", {
            "fields": (
                "created_at",
                "updated_at"
            )
        })
    )


admin.site.unregister(FlatPage)
admin.site.register(Page, PageAdmin)
