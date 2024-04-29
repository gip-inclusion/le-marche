from django.contrib import admin
from django.http import HttpResponseRedirect

from lemarche.conversations.models import Conversation, TemplateTransactional
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
    list_display = [
        "id",
        "uuid",
        "sender_encoded",
        "is_validate",
        "title",
        "kind",
        "answer_count_annotated",
        "created_at",
    ]
    list_filter = ["kind", HasAnswerFilter, IsValidatedFilter]
    search_fields = ["id", "uuid", "sender_email"]
    search_help_text = "Cherche sur les champs : ID, UUID, Initiateur (E-mail)"

    exclude = ["data"]
    readonly_fields = [
        "id",
        "uuid",
        "sender_encoded",
        "title",
        "version",
        "siae",
        "sender_first_name",
        "sender_last_name",
        "sender_email",
        "answer_count_annotated",
        "data_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {"fields": ("uuid", "sender_encoded", "title", "initial_body_message")},
        ),
        ("Interlocuteurs", {"fields": ("sender_first_name", "sender_last_name", "sender_email", "siae")}),
        (
            "Contenu de la conversation",
            {
                "fields": (
                    "answer_count_annotated",
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
        qs = qs.with_answer_stats()
        return qs

    def is_validate(self, conversation: Conversation):
        return conversation.validated_at is not None

    is_validate.boolean = True
    is_validate.short_description = "Validé"

    def answer_count_annotated(self, conversation):
        return getattr(conversation, "answer_count_annotated", 0)

    answer_count_annotated.short_description = "Nombre de réponses"
    answer_count_annotated.admin_order_field = "answer_count_annotated"

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


@admin.register(TemplateTransactional, site=admin_site)
class TemplateTransactionalAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "code", "mailjet_id", "brevo_id", "source", "is_active", "created_at", "updated_at"]
    search_fields = ["id", "name", "code", "mailjet_id", "brevo_id"]

    readonly_fields = ["code", "email_subject", "email_from_email", "email_from_name", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("name", "code", "description")}),
        ("Paramètres de l'e-mail", {"fields": ("email_subject", "email_from_email", "email_from_name")}),
        ("Paramètres d'envoi", {"fields": ("mailjet_id", "brevo_id", "source", "is_active")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )
