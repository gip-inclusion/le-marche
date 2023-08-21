from django.contrib import admin

from lemarche.conversations.models import Conversation
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import pretty_print_readonly_jsonfield_to_table


@admin.register(Conversation, site=admin_site)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "uuid", "title", "kind", "answer_count", "created_at"]
    list_filter = ["kind"]
    search_fields = ["id", "uuid", "sender_email"]
    search_help_text = "Cherche sur les champs : ID, UUID, Initiateur (E-mail)"

    exclude = ["data"]
    readonly_fields = [
        "id",
        "uuid",
        "title",
        "version",
        "siae",
        "sender_first_name",
        "sender_last_name",
        "sender_email",
        "answer_count",
        "data_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {"fields": ("uuid", "title", "initial_body_message")},
        ),
        ("Interlocuteurs", {"fields": ("sender_first_name", "sender_last_name", "sender_email", "siae")}),
        (
            "Contenu de la conversation",
            {
                "fields": (
                    "answer_count",
                    "data_display",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    class Media:
        js = ("js/filter_data_message.js",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_answer_count()
        return qs

    def answer_count(self, conversation):
        return getattr(conversation, "answer_count", 0)

    answer_count.short_description = "Nombre de réponses"
    answer_count.admin_order_field = "answer_count"

    def data_display(self, conversation: Conversation = None):
        if conversation:
            return pretty_print_readonly_jsonfield_to_table(conversation.data, id_table="table_filter_data_message")
        return "-"

    data_display.short_description = "Messages de la conversation"
