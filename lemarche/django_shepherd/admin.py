# admin.py
from django.contrib import admin

from lemarche.utils.admin.admin_site import admin_site

from .models import GuideStep, UserGuide


class GuideStepInline(admin.TabularInline):
    model = GuideStep
    extra = 1


@admin.register(UserGuide, site=admin_site)
class UserGuideAdmin(admin.ModelAdmin):
    inlines = [GuideStepInline]
