from django.contrib import admin

from lemarche.conversations.models import Conversation
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import print_readonly_jsonfield


@admin.register(Conversation, site=admin_site)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "uuid", "kind", "created_at"]
    search_fields = ["id", "uuid"]
    search_help_text = "Cherche sur les champs : ID, UUID"
    exclude = ["data"]
    readonly_fields = ["id", "uuid", "title", "version", "siae", "email_sender", "created_at", "data_display"]

    def data_display(self, conversation: Conversation = None):
        if conversation:
            return print_readonly_jsonfield(conversation.data, id_table="table_filter_data_message")
        return "-"

    class Media:
        js = ("js/filter_data_message.js",)

    data_display.short_description = "Messages de la conversation"
