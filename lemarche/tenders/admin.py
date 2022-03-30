from django.contrib import admin

from lemarche.tenders.models import Tender


# Register your models here.
@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "author",
        "kind",
        "deadline_date",
        "start_working_date",
        "response_kind",
        "nb_siae_email_send",
        "nb_siae_detail_display",
        "nb_siae_contact_click",
        "created_at",
    ]
    list_filter = ["kind", "deadline_date", "start_working_date", "response_kind"]
    # filter on "perimeters"? (loads ALL the perimeters... Use django-admin-autocomplete-filter instead?)
    search_fields = ["id", "title"]
    search_help_text = "Cherche sur les champs : ID, Titre"
    readonly_fields = [
        "nb_siae_email_send",
        "nb_siae_detail_display",
        "nb_siae_contact_click",
        "created_at",
        "updated_at",
    ]

    autocomplete_fields = ["perimeters", "sectors"]

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "slug", "kind"),
            },
        ),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "constraints",
                    "perimeters",
                    "sectors",
                    "external_link",
                    "amount",
                    "response_kind",
                    "deadline_date",
                    "start_working_date",
                ),
            },
        ),
        (
            "Contact",
            {
                "fields": ("author", "contact_first_name", "contact_last_name", "contact_email", "contact_phone"),
            },
        ),
        (
            "Stats",
            {
                "fields": ("nb_siae_email_send", "nb_siae_detail_display", "nb_siae_contact_click"),
            },
        ),
        ("Info", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        return qs

    def nb_siae_email_send(self, tender):
        return tender.siae_email_send_count

    nb_siae_email_send.short_description = "Structures contactées"
    nb_siae_email_send.admin_order_field = "siae_email_send_count"

    def nb_siae_detail_display(self, tender):
        return tender.siae_detail_display_count

    nb_siae_detail_display.short_description = "Structures vues"
    nb_siae_detail_display.admin_order_field = "siae_detail_display_count"

    def nb_siae_contact_click(self, tender):
        return tender.siae_contact_click_count

    nb_siae_contact_click.short_description = "Structures intéressées"
    nb_siae_contact_click.admin_order_field = "siae_contact_click_count"
