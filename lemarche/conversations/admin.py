from django.contrib import admin

from lemarche.conversations.models import Conversation
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import pretty_print_readonly_jsonfield


@admin.register(Conversation, site=admin_site)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "uuid", "kind", "created_at"]
    search_fields = ["id", "uuid"]
    search_help_text = "Cherche sur les champs : ID, UUID"
    exclude = ["data"]
    readonly_fields = ["created_at", "data_display"]

    def data_display(self, conversation: Conversation = None):
        if conversation:
            return pretty_print_readonly_jsonfield(conversation.data)
        return "-"

    data_display.short_description = Conversation._meta.get_field("data").verbose_name
