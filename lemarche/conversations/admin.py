from django.contrib import admin
from django.http import HttpResponseRedirect

from lemarche.conversations.models import Conversation
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import pretty_print_readonly_jsonfield_to_table
from lemarche.www.conversations.tasks import send_first_email_from_conversation


class HasAnswerFilter(admin.SimpleListFilter):
    """Custom admin filter to target conversations who have an answer."""

    title = "Avec réponse ?"
    parameter_name = "has_answer"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_answer()
        elif value == "No":
            return queryset.filter(data=[])
        return queryset


class IsValidatedFilter(admin.SimpleListFilter):
    """Custom admin filter to target conversations who is validated."""

    title = "Validée ?"
    parameter_name = "is_validate"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.filter(validated_at__isnull=False)
        elif value == "No":
            return queryset.filter(validated_at__isnull=True)
        return queryset


@admin.register(Conversation, site=admin_site)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "uuid", "is_validate", "title", "kind", "answer_count", "created_at"]
    list_filter = ["kind", HasAnswerFilter, IsValidatedFilter]
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

    change_form_template = "conversations/admin_change_form.html"

    class Media:
        js = ("js/filter_data_message.js",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_answer_count()
        return qs

    def is_validate(self, conversation: Conversation):
        return conversation.validated_at is not None

    is_validate.boolean = True
    is_validate.short_description = "Validé"

    def answer_count(self, conversation):
        return getattr(conversation, "answer_count", 0)

    answer_count.short_description = "Nombre de réponses"
    answer_count.admin_order_field = "answer_count"

    def response_change(self, request, obj: Conversation):
        if request.POST.get("_validate_conversation"):
            obj.set_validated()
            send_first_email_from_conversation(obj)
            self.message_user(request, "La conversation a été validé et envoyé à la structure")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def data_display(self, conversation: Conversation = None):
        if conversation:
            return pretty_print_readonly_jsonfield_to_table(conversation.data, id_table="table_filter_data_message")
        return "-"

    data_display.short_description = "Messages de la conversation"
