from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.db import models

from lemarche.utils.admin.admin_site import admin_site

from .models import GuideStep, UserGuide


class GuideStepInline(admin.TabularInline):
    model = GuideStep
    extra = 1
    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget(config_name="frontuser")},
    }


@admin.register(UserGuide, site=admin_site)
class UserGuideAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "description",
        "created_at",
    ]

    inlines = [GuideStepInline]

    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget(config_name="frontuser")},
    }
