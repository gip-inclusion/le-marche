from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.db import models

from lemarche.common.admin import admin_site
from lemarche.pages.models import Page, PageFragment


@admin.register(Page, site=admin_site)
class PageAdmin(FlatPageAdmin):
    list_display = ["url", "title", "created_at", "updated_at"]

    readonly_fields = ["created_at", "updated_at"]
    formfield_overrides = {models.TextField: {"widget": CKEditorWidget}}

    fieldsets = (
        (
            None,
            {
                "fields": ("url", "title", "content"),
            },
        ),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PageFragment, site=admin_site)
class PageFragmentAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at", "updated_at"]

    readonly_fields = ["created_at", "updated_at"]
    formfield_overrides = {models.TextField: {"widget": CKEditorWidget}}

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "content"),
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_readonly_fields(self, request, obj=None):
        # title cannot be changed (to avoid query errors)
        if obj:
            return self.readonly_fields + ["title"]
        return self.readonly_fields
