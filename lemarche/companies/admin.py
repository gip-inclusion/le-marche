from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, mark_safe
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from lemarche.companies.models import Company, CompanyLabel, CompanySiaeClientReferenceMatch
from lemarche.utils.admin.admin_site import admin_site


class HasUserFilter(admin.SimpleListFilter):
    title = "Avec des utilisateurs ?"
    parameter_name = "has_user"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_user()
        elif value == "No":
            return queryset.filter(users__isnull=True)
        return queryset


class HasEmailDomainFilter(admin.SimpleListFilter):
    title = "Avec des noms de domaine d'e-mails ?"
    parameter_name = "has_email_domain"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_email_domain()
        elif value == "No":
            return queryset.filter(email_domain_list=[])
        return queryset


class ModerationStatusFilter(admin.SimpleListFilter):
    title = "Statut de modération"
    parameter_name = "moderation_status"

    def lookups(self, request, model_admin):
        return CompanySiaeClientReferenceMatch.ModerationStatus.choices

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(moderation_status=value)
        return queryset


@admin.register(CompanyLabel, site=admin_site)
class CompanyLabelAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID et nom"
    ordering = ["name"]


@admin.register(Company, site=admin_site)
class CompanyAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = [
        "id",
        "name",
        "user_count_annotated_with_link",
        "user_tender_count_annotated_with_link",
        "created_at",
    ]
    list_filter = [HasUserFilter, HasEmailDomainFilter]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    readonly_fields = [
        "logo_url_display",
        "user_count_annotated_with_link",
        "user_tender_count_annotated_with_link",
    ] + Company.READONLY_FIELDS

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "description", "siret", "website", "email_domain_list", "labels"),
            },
        ),
        ("Logo", {"fields": ("logo_url", "logo_url_display")}),
        ("LinkedIn", {"fields": ("linkedin_buyer_count",)}),
        ("Impact", {"fields": ("user_count_annotated_with_link", "user_tender_count_annotated_with_link")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_user_stats()
        qs = qs.order_by("name")
        return qs

    def get_readonly_fields(self, request, obj=None):
        # slug cannot be changed (to avoid query errors)
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

    def user_count_annotated_with_link(self, company):
        url = reverse("admin:users_user_changelist") + f"?company__id__exact={company.id}"
        return format_html(f'<a href="{url}">{company.user_count_annotated}</a>')

    user_count_annotated_with_link.short_description = "Utilisateurs rattachés"
    user_count_annotated_with_link.admin_order_field = "user_count_annotated"

    def user_tender_count_annotated_with_link(self, company):
        url = reverse("admin:tenders_tender_changelist") + f"?author__company_id__exact={company.id}"
        return format_html(f'<a href="{url}">{company.user_tender_count_annotated}</a>')

    user_tender_count_annotated_with_link.short_description = "Besoins déposés par les utilisateurs"
    user_tender_count_annotated_with_link.admin_order_field = "user_tender_count_annotated"


@admin.register(CompanySiaeClientReferenceMatch, site=admin_site)
class CompanySiaeClientReferenceMatchAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "company__name",
        "siae_client_reference__name",
        "similarity_score_display",
        "moderation_status",
        "moderated_by",
        "created_at",
    ]
    list_filter = [ModerationStatusFilter, "created_at", "moderated_at"]
    search_fields = [
        "company__name",
        "siae_client_reference__name",
        "company_name",
        "client_reference_name",
    ]
    search_help_text = "Cherche sur les champs : Nom entreprise, Nom référence client"

    readonly_fields = [
        "company_with_link",
        "client_reference_with_link",
        "similarity_score_display",
        "company_name",
        "client_reference_name",
        "moderated_by",
        "moderated_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Correspondance",
            {
                "fields": (
                    "company_with_link",
                    "client_reference_with_link",
                    "similarity_score_display",
                    "company_name",
                    "client_reference_name",
                )
            },
        ),
        (
            "Modération",
            {
                "fields": (
                    "moderation_status",
                    "moderated_by",
                    "moderated_at",
                    "moderation_notes",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    actions = ["approve_matches", "reject_matches"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "siae_client_reference", "moderated_by")

    def company_with_link(self, match):
        if match.company:
            url = reverse("admin:companies_company_change", args=[match.company.id])
            return format_html(f'<a href="{url}">{match.company.name}</a>')
        return match.company_name

    company_with_link.short_description = "Entreprise"
    company_with_link.admin_order_field = "company__name"

    def client_reference_with_link(self, match):
        if match.siae_client_reference:
            url = reverse("admin:siaes_siaeclientreference_change", args=[match.siae_client_reference.id])
            return format_html(f'<a href="{url}">{match.siae_client_reference.name}</a>')
        return match.client_reference_name

    client_reference_with_link.short_description = "Référence client"
    client_reference_with_link.admin_order_field = "siae_client_reference__name"

    def similarity_score_display(self, match):
        return f"{match.similarity_score:.3f}"

    similarity_score_display.short_description = "Score de similarité"
    similarity_score_display.admin_order_field = "similarity_score"

    def approve_matches(self, request, queryset):
        updated = queryset.update(moderation_status="approved", moderated_by=request.user, moderated_at=timezone.now())
        self.message_user(request, f"{updated} correspondance(s) approuvée(s).")

    approve_matches.short_description = "Approuver les correspondances sélectionnées"

    def reject_matches(self, request, queryset):
        updated = queryset.update(moderation_status="rejected", moderated_by=request.user, moderated_at=timezone.now())
        self.message_user(request, f"{updated} correspondance(s) rejetée(s).")

    reject_matches.short_description = "Rejeter les correspondances sélectionnées"

    def save_model(self, request, obj, form, change):
        """
        Automatically update moderated_by and moderated_at when moderation_status changes
        """
        if change:  # Only for existing objects
            # Get the original object from database
            original_obj = self.model.objects.get(pk=obj.pk)

            # Check if moderation_status has changed
            if original_obj.moderation_status != obj.moderation_status:
                obj.moderated_by = request.user
                obj.moderated_at = timezone.now()

        super().save_model(request, obj, form, change)
