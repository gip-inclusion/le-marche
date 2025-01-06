import re

from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from fieldsets_with_inlines import FieldsetsInlineMixin

from lemarche.conversations.models import TemplateTransactionalSendLog
from lemarche.notes.models import Note
from lemarche.siaes.models import Siae, SiaeUser
from lemarche.users.forms import UserChangeForm, UserCreationForm
from lemarche.users.models import User
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.fields import pretty_print_readonly_jsonfield


class HasCompanyFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who are linked to a Company."""

    title = "Rattaché à une entreprise ?"
    parameter_name = "has_company"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_company()
        elif value == "No":
            return queryset.filter(company__isnull=True)
        return queryset


class HasSiaeFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who are linked to a Siae."""

    title = "Gestionnaire de structure ?"
    parameter_name = "has_siae"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_siae()
        elif value == "No":
            return queryset.filter(siaes__isnull=True)
        return queryset


class HasTenderFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who have tenders."""

    title = "Besoin déposé ?"
    parameter_name = "has_tender"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_tender()
        elif value == "No":
            return queryset.filter(tenders__isnull=True)
        return queryset


class HasFavoriteListFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who have favorite lists."""

    title = "Listes d'achats favoris ?"
    parameter_name = "has_favorite_list"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_favorite_list()
        elif value == "No":
            return queryset.filter(favorite_lists__isnull=True)
        return queryset


class HasPartnerNetworkFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who have a partner_network."""

    title = "Partenaire avec réseau ?"
    parameter_name = "has_partner_network"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_partner_network()
        elif value == "No":
            return queryset.filter(partner_network__isnull=True)
        return queryset


class HasApiKeyFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who have a api_key."""

    title = "Clé API ?"
    parameter_name = "has_api_key"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_api_key()
        elif value == "No":
            return queryset.filter(api_key__isnull=True)
        return queryset


class IsAnonymizedFilter(admin.SimpleListFilter):
    """Custom admin filter to target users who are anonymized"""

    title = "Est anonymisé"
    parameter_name = "is_anonymized"

    def lookups(self, request, model_admin):
        return ("Yes", "Oui"), (None, "Non")

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.filter(is_anonymized=True)
        return queryset.filter(is_anonymized=False)

    def choices(self, changelist):
        """Removed the first yield from the base method to only have 2 choices, defaulting too No"""
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }


class UserNoteInline(GenericTabularInline):
    model = Note
    fields = ["text", "author", "created_at", "updated_at"]
    readonly_fields = ["author", "created_at", "updated_at"]
    extra = 1

    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget(config_name="admin_note_text")},
    }


class SiaeUserInline(admin.TabularInline):
    model = SiaeUser
    fields = ["siae", "siae_with_link", "created_at", "updated_at"]
    autocomplete_fields = ["siae"]
    readonly_fields = ["siae_with_link", "created_at", "updated_at"]
    extra = 0

    def siae_with_link(self, siae_user):
        url = reverse("admin:siaes_siae_change", args=[siae_user.siae_id])
        return format_html(f'<a href="{url}">{siae_user.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name


@admin.register(User, site=admin_site)
class UserAdmin(FieldsetsInlineMixin, UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = [
        "id",
        "first_name",
        "last_name",
        "kind",
        "company_name",
        "siae_count_annotated_with_link",
        "tender_count_annotated_with_link",
        "last_login",
        "created_at",
    ]
    list_filter = [
        "kind",
        HasCompanyFilter,
        HasSiaeFilter,
        HasTenderFilter,
        "buyer_kind",
        "partner_kind",
        HasPartnerNetworkFilter,
        "can_display_tender_contact_details",
        HasFavoriteListFilter,
        HasApiKeyFilter,
        "is_staff",
        "is_superuser",
        IsAnonymizedFilter,
    ]
    search_fields = ["id", "email", "first_name", "last_name"]
    search_help_text = "Cherche sur les champs : ID, E-mail, Prénom, Nom"
    ordering = ["-created_at"]
    actions = ["anonymize_users"]

    autocomplete_fields = ["company", "partner_network"]
    readonly_fields = (
        [field.name for field in User._meta.fields if field.name.startswith("c4_")]
        + [field for field in User.READONLY_FIELDS]
        + [
            "siae_count_annotated_with_link",
            "tender_count_annotated_with_link",
            "favorite_list_count_with_link",
            "recipient_transactional_send_logs_count_with_link",
            "brevo_contact_id",
            "extra_data_display",
        ]
    )

    fieldsets_with_inlines = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "kind",
                    "phone",
                    "company",
                    "company_name",
                    "position",
                    "buyer_kind",
                    "buyer_kind_detail",
                    "partner_kind",
                    "partner_network",
                )
            },
        ),
        UserNoteInline,
        SiaeUserInline,
        (
            "Dépôt de besoin",
            {
                "fields": (
                    "tender_count_annotated_with_link",
                    "can_display_tender_contact_details",
                ),
            },
        ),
        (
            "Listes d'achats favoris",
            {
                "fields": ("favorite_list_count_with_link",),
            },
        ),
        (
            "RGPD & co",
            {
                "fields": (
                    "accept_rgpd",
                    "accept_survey",
                    "accept_share_contact_to_external_partners",
                    "source",
                )
            },
        ),
        ("API", {"fields": ("api_key", "api_key_last_updated")}),
        (
            "Permissions",
            {"classes": ["collapse"], "fields": ("is_active", "is_staff", "is_superuser", "groups")},
        ),
        (
            "Stats",
            {
                "classes": ["collapse"],
                "fields": (
                    "dashboard_last_seen_date",
                    "tender_list_last_seen_date",
                    "recipient_transactional_send_logs_count_with_link",
                    "brevo_contact_id",
                    "extra_data_display",
                ),
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "kind",
                    "phone",
                )
            },
        ),
        ("API", {"fields": ("api_key",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        qs = qs.with_tender_stats()
        return qs

    def get_search_results(self, request, queryset, search_term):
        """
        We have a usecase where we want to return only admins
        We need to match strings like:
        - /admin/autocomplete/?app_label=tenders&model_name=tender&field_name=admins
        - /admin/autocomplete/?term=raph&app_label=tenders&model_name=tender&field_name=admins
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        pattern = r"^\/admin\/autocomplete\/\?.*app_label=tenders&model_name=tender&field_name=admins$"
        if re.search(pattern, request.get_full_path()):
            queryset = queryset.is_admin_bizdev()
        return queryset, use_distinct

    def get_urls(self):
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_urls
        urls = super().get_urls()
        my_urls = [
            path("anonymise_users/", self.admin_site.admin_view(self.anonymize_users_view), name="anonymize_users"),
            *urls,  # these patterns last, because they can match a lot of urls
        ]
        return my_urls

    def anonymize_users_view(self, request):
        """Confirmation page after selecting users to anonymize."""

        if request.method == "GET":
            # Display confirmation page
            ids = request.GET.getlist("user_id")
            queryset = self.model.objects.filter(id__in=ids)
            context = {
                # Include common variables for rendering the admin template.
                **self.admin_site.each_context(request),
                "opts": self.opts,
                "queryset": queryset,
            }
            return TemplateResponse(request, "admin/anonymize_confirmation.html", context)
        if request.method == "POST":
            # anonymize users
            ids = request.POST.getlist("user_id")
            queryset = self.model.objects.filter(id__in=ids)

            queryset.exclude(id=request.user.id).anonymize_update()
            SiaeUser.objects.filter(user__is_anonymized=True).delete()

            self.message_user(request, "L'anonymisation s'est déroulée avec succès")

            return HttpResponseRedirect(reverse("admin:users_user_changelist"))

    def save_formset(self, request, form, formset, change):
        """
        Set Note author on create
        """
        for form in formset:
            if type(form.instance) is Note:
                if not form.instance.id and form.instance.text and change:
                    form.instance.author = request.user
        super().save_formset(request, form, formset, change)

    def siae_count_annotated_with_link(self, user):
        url = reverse("admin:siaes_siae_changelist") + f"?users__in={user.id}"
        return format_html(f'<a href="{url}">{getattr(user, "siae_count_annotated", 0)}</a>')

    siae_count_annotated_with_link.short_description = "Nombre de structures"
    siae_count_annotated_with_link.admin_order_field = "siae_count_annotated"

    def tender_count_annotated_with_link(self, user):
        url = reverse("admin:tenders_tender_changelist") + f"?author__id__exact={user.id}"
        return format_html(f'<a href="{url}">{getattr(user, "tender_count_annotated", 0)}</a>')

    tender_count_annotated_with_link.short_description = "Nombre de besoins déposés"
    tender_count_annotated_with_link.admin_order_field = "tender_count_annotated"

    def favorite_list_count_with_link(self, user):
        url = reverse("admin:favorites_favoritelist_changelist") + f"?users__in={user.id}"
        return format_html(f'<a href="{url}">{user.favorite_list_count}</a>')

    favorite_list_count_with_link.short_description = "Nombre de listes de favoris"
    favorite_list_count_with_link.admin_order_field = "favorite_list_count"

    def recipient_transactional_send_logs_count_with_link(self, obj):
        url = reverse("admin:conversations_templatetransactionalsendlog_changelist") + f"?user__id__exact={obj.id}"
        return format_html(f'<a href="{url}">{obj.recipient_transactional_send_logs.count()}</a>')

    recipient_transactional_send_logs_count_with_link.short_description = (
        TemplateTransactionalSendLog._meta.verbose_name
    )

    def extra_data_display(self, instance: User = None):
        if instance:
            return pretty_print_readonly_jsonfield(instance.extra_data)
        return "-"

    extra_data_display.short_description = User._meta.get_field("extra_data").verbose_name

    @admin.action(description="Anonymiser les utilisateurs sélectionnés")
    def anonymize_users(self, request, queryset):
        """Wipe personal data of all selected users and unlink from SiaeUser
        The logged user is excluded to avoid any mistakes"""
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/actions/#actions-that-provide-intermediate-pages

        selected = queryset.values_list("pk", flat=True)
        return HttpResponseRedirect(
            f"{reverse('admin:anonymize_users')}?{'&'.join(f'user_id={str(pk)}' for pk in selected)}"
        )
