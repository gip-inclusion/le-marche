from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from lemarche.labels.models import Label
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import pretty_print_readonly_jsonfield


@admin.register(Label, site=admin_site)
class LabelAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_count_annotated_with_link", "created_at"]
    search_fields = ["id", "name", "description"]
    search_help_text = "Cherche sur les champs : ID, Nom, Description"

    readonly_fields = [
        "siae_count_annotated_with_link",
        "logo_url_display",
        "data_last_sync_date",
        "logs_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "description", "website"),
            },
        ),
        ("Logo", {"fields": ("logo_url", "logo_url_display")}),
        ("Structures", {"fields": ("siae_count_annotated_with_link",)}),
        (
            "Source de données",
            {
                "fields": (
                    "data_description",
                    "data_last_sync_date",
                )
            },
        ),
        ("Stats", {"fields": ("logs_display",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        return qs

    def get_readonly_fields(self, request, obj=None):
        # slug cannot be changed after creation
        if obj:
            return self.readonly_fields + ["slug"]
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        # set slug on create
        if not obj:
            return {"slug": ("name",)}
        return {}

    def logo_url_display(self, instance):
        if instance.logo_url:
            return mark_safe(
                f'<a href="{instance.logo_url}" target="_blank">'
                f'<img src="{instance.logo_url}" title="{instance.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"

    def logs_display(self, label=None):
        if label:
            return pretty_print_readonly_jsonfield(label.logs)
        return "-"

    logs_display.short_description = Label._meta.get_field("logs").verbose_name

    def siae_count_annotated_with_link(self, label):
        url = reverse("admin:siaes_siae_changelist") + f"?labels__id__exact={label.id}"
        return format_html(f'<a href="{url}">{label.siae_count_annotated}</a>')

    siae_count_annotated_with_link.short_description = "Nombre de structures"
    siae_count_annotated_with_link.admin_order_field = "siae_count_annotated"
