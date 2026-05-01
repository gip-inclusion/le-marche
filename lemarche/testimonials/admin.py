from django.contrib import admin
from django.utils import timezone

from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial


class StatusFilter(admin.SimpleListFilter):
    title = "Statut"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return testimonial_constants.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(SiaeTestimonial)
class SiaeTestimonialAdmin(admin.ModelAdmin):
    list_display = ["id", "siae", "client_email", "author_display_name", "status", "submitted_at", "published_at"]
    list_filter = [StatusFilter, "siae"]
    search_fields = ["client_email", "siae__name", "content"]
    raw_id_fields = ["siae", "buyer_user"]
    readonly_fields = [
        "token",
        "sent_at",
        "token_expires_at",
        "submitted_at",
        "published_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Invitation",
            {
                "fields": [
                    "siae",
                    "client_email",
                    "custom_message",
                    "token",
                    "sent_at",
                    "token_expires_at",
                    "status",
                ]
            },
        ),
        (
            "Témoignage reçu",
            {
                "fields": [
                    "content",
                    "author_first_name",
                    "author_last_name",
                    "author_organization",
                    "buyer_user",
                    "submitted_at",
                    "published_at",
                ]
            },
        ),
        (
            "Métadonnées",
            {"fields": ["created_at", "updated_at"]},
        ),
    ]
    actions = ["action_publish", "action_reject"]

    @admin.action(description="Publier les témoignages sélectionnés")
    def action_publish(self, request, queryset):
        count = 0
        for testimonial in queryset.is_submitted():
            testimonial.publish()
            count += 1
        self.message_user(request, f"{count} témoignage(s) publié(s).")

    @admin.action(description="Rejeter les témoignages sélectionnés")
    def action_reject(self, request, queryset):
        count = queryset.is_submitted().count()
        queryset.is_submitted().update(status=testimonial_constants.STATUS_REJECTED, updated_at=timezone.now())
        self.message_user(request, f"{count} témoignage(s) rejeté(s).")
