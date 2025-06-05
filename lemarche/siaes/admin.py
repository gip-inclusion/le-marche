from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.gis import admin as gis_admin
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from simple_history.admin import SimpleHistoryAdmin

from lemarche.conversations.models import Conversation, TemplateTransactionalSendLog
from lemarche.labels.models import Label
from lemarche.networks.models import Network
from lemarche.notes.models import Note
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import (
    Siae,
    SiaeActivity,
    SiaeClientReference,
    SiaeGroup,
    SiaeImage,
    SiaeLabel,
    SiaeLabelOld,
    SiaeOffer,
    SiaeUser,
    SiaeUserRequest,
)
from lemarche.users.models import User
from lemarche.utils.admin.actions import export_as_xls
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.admin.inline_fieldset import FieldsetsInlineMixin
from lemarche.utils.fields import ChoiceArrayField, pretty_print_readonly_jsonfield


class IsLiveFilter(admin.SimpleListFilter):
    """Custom admin filter to target siaes who are live (active and not delisted)."""

    title = "Live ? (active et non masquée)"
    parameter_name = "is_live"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.is_live()
        elif value == "No":
            return queryset.is_not_live()
        return queryset


class HasUserFilter(admin.SimpleListFilter):
    """Custom admin filter to target siaes who have at least 1 user."""

    title = "Avec un gestionnaire ?"
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


class SiaeActivityInline(admin.TabularInline):
    model = SiaeActivity
    fields = [
        "sectors",
        "presta_type",
        # "location", # FIXME: see why activity location loads all perimeters
        "geo_range",
        "geo_range_custom_distance",
        "created_at",
    ]
    show_change_link = True
    can_delete = False
    extra = 0
    max_num = 0

    def has_change_permission(self, request, obj=None):
        return False


class SiaeLabelInline(admin.TabularInline):
    model = SiaeLabel
    fields = ["label", "label_with_link", "created_at", "updated_at"]
    autocomplete_fields = ["label"]
    readonly_fields = ["label_with_link", "created_at", "updated_at"]
    extra = 0

    def label_with_link(self, siae_label):
        url = reverse("admin:labels_label_change", args=[siae_label.label_id])
        return format_html(f'<a href="{url}">{siae_label.label}</a>')

    label_with_link.short_description = Label._meta.verbose_name


class SiaeNoteInline(GenericTabularInline):
    model = Note
    fields = ["text", "author", "created_at", "updated_at"]
    readonly_fields = ["author", "created_at", "updated_at"]
    extra = 1

    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget(config_name="admin_note_text")},
    }


class SiaeUserFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        """Check for duplcated m2m to avoid raising IntegrityError"""
        user_list = []

        for form in self.forms:
            if form.cleaned_data:
                user_list.append(form.cleaned_data["user"])

        duplicated_groups = [x for x in user_list if user_list.count(x) > 1]
        if duplicated_groups:
            raise ValidationError(
                "Gestionnaires dupliqués: %(duplicates)s",
                params={"duplicates": ", ".join(group.__str__() for group in set(duplicated_groups))},
            )


class SiaeUserInline(admin.TabularInline):
    model = SiaeUser
    fields = ["user", "user_with_link", "created_at", "updated_at"]
    autocomplete_fields = ["user"]
    readonly_fields = ["user_with_link", "created_at", "updated_at"]
    formset = SiaeUserFormset
    extra = 0

    def user_with_link(self, siae_user):
        url = reverse("admin:users_user_change", args=[siae_user.user_id])
        return format_html(f'<a href="{url}">{siae_user.user}</a>')

    user_with_link.short_description = User._meta.verbose_name


class ConversationsInline(admin.TabularInline):
    model = Conversation
    fields = ["id", "title_with_link", "nb_message_with_link", "kind", "created_at"]
    # autocomplete_fields = ["user"]
    readonly_fields = ["id", "title_with_link", "nb_message_with_link", "kind", "created_at"]
    show_change_link = True
    can_delete = False
    extra = 0
    max_num = 0

    def title_with_link(self, conversation: Conversation):
        url = reverse("admin:conversations_conversation_change", args=[conversation.id])
        return format_html(f'<a href="{url}">{conversation.title}</a>')

    title_with_link.short_description = "Titre"

    def nb_message_with_link(self, conversation: Conversation):
        url = reverse("admin:conversations_conversation_change", args=[conversation.id])
        return format_html(f'<a href="{url}">{conversation.nb_messages}</a>')

    nb_message_with_link.short_description = "Nombre de messages"


@admin.register(Siae, site=admin_site)
class SiaeAdmin(FieldsetsInlineMixin, gis_admin.GISModelAdmin, SimpleHistoryAdmin):
    # GISModelAdmin param for coords fields
    actions = [export_as_xls]
    list_display = [
        "id",
        "name",
        "siret",
        "kind",
        "city",
        "super_badge",
        "user_count_with_link",
        "tender_email_send_count_annotated_with_link",
        "tender_detail_display_count_annotated_with_link",
        "tender_detail_contact_click_count_annotated_with_link",
        "tender_detail_not_interested_count_annotated_with_link",
        "activity_count_with_link",
        "offer_count_with_link",
        "label_count_with_link",
        "client_reference_count_with_link",
        "image_count_with_link",
        "created_at",
    ]
    list_filter = [
        IsLiveFilter,
        "is_delisted",
        "is_first_page",
        HasUserFilter,
        "kind",
        "super_badge",
        "source",
        "networks",
    ]
    search_fields = ["id", "name", "brand", "slug", "siret"]
    search_help_text = "Cherche sur les champs : ID, Raison sociale, Enseigne, Slug, Siret"

    autocomplete_fields = ["networks", "groups"]
    readonly_fields = (
        [field for field in Siae.READONLY_FIELDS if field not in ("coords")]
        + [f"{field}_last_updated" for field in Siae.TRACK_UPDATE_FIELDS if field not in ("address")]
        + [
            "siren",
            "sector_count_with_link",
            "network_count_with_link",
            "group_count_with_link",
            "activity_count_with_link",
            "offer_count_with_link",
            "label_count_with_link",
            "client_reference_count_with_link",
            "user_count_with_link",
            "image_count_with_link",
            "coords_display",
            "logo_url",
            "logo_url_display",
            "tender_count_annotated_with_link",
            "tender_email_send_count_annotated_with_link",
            "tender_email_link_click_count_annotated_with_link",
            "tender_detail_display_count_annotated_with_link",
            "tender_detail_contact_click_count_annotated_with_link",
            "tender_detail_not_interested_count_annotated_with_link",
            "recipient_transactional_send_logs_count_with_link",
            "brevo_company_id",
            "extra_data_display",
            "import_raw_object_display",
            "logs_display",
        ]
    )
    formfield_overrides = {
        ChoiceArrayField: {"widget": forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox-select-multiple"})},
    }

    modifiable = False

    fieldsets_with_inlines_original = [
        (
            "Affichage",
            {
                "fields": ("is_active", "is_delisted", "is_first_page"),
            },
        ),
        (
            "Données C1 (ou ESAT ou SEP)",
            {
                "fields": (
                    "name",
                    "slug",
                    "brand",
                    "siret",
                    "siren",
                    "etablissement_count",
                    "naf",
                    "kind",
                    "nature",
                    "c1_id",
                    "asp_id",
                    "website",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "post_code",
                    "department",
                    "region",
                    "coords_display",
                    "coords",
                    "source",
                )
            },
        ),
        ("Données C2", {"fields": Siae.FIELDS_FROM_C2}),
        ("Données API Entreprise", {"fields": Siae.FIELDS_FROM_API_ENTREPRISE}),
        (
            "Données API QPV (Quartier prioritaire de la politique de la ville)",
            {"fields": Siae.FIELDS_FROM_QPV},
        ),
        ("Données API ZRR (Zone de revitalisation rurale)", {"fields": Siae.FIELDS_FROM_ZRR}),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "sector_count_with_link",
                    "activity_count_with_link",
                    "offer_count_with_link",
                    "label_count_with_link",
                    "client_reference_count_with_link",
                    "image_count_with_link",
                    "completion_rate",
                )
            },
        ),
        SiaeActivityInline,
        SiaeLabelInline,
        (
            "Contact",
            {
                "fields": (
                    "contact_first_name",
                    "contact_last_name",
                    "contact_email",
                    "contact_phone",
                    "contact_website",
                    "contact_social_website",
                    "user_count_with_link",
                )
            },
        ),
        (
            "Réseaux & Groupements",
            {
                "fields": (
                    "networks",
                    "network_count_with_link",
                    "groups",
                    "group_count_with_link",
                )
            },
        ),
        SiaeNoteInline,
        ConversationsInline,
        SiaeUserInline,
        (
            "Logo",
            {
                "fields": (
                    "logo_url",
                    "logo_url_display",
                )
            },
        ),
        (
            "Besoins des acheteurs",
            {
                "fields": (
                    "tender_count_annotated_with_link",
                    "tender_email_send_count_annotated_with_link",
                    "tender_email_link_click_count_annotated_with_link",
                    "tender_detail_display_count_annotated_with_link",
                    "tender_detail_contact_click_count_annotated_with_link",
                    "tender_detail_not_interested_count_annotated_with_link",
                )
            },
        ),
        (
            "Badge 'Super prestataire inclusif'",
            {
                "fields": (
                    "super_badge",
                    "super_badge_last_updated",
                )
            },
        ),
        (
            "Stats",
            {
                "classes": ["collapse"],
                "fields": (
                    "signup_date",
                    "content_filled_basic_date",
                    "recipient_transactional_send_logs_count_with_link",
                    "brevo_company_id",
                    "extra_data_display",
                ),
            },
        ),
        ("Si importé", {"classes": ["collapse"], "fields": ("import_raw_object_display",)}),
        ("Logs", {"classes": ["collapse"], "fields": ("logs_display",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    ]

    # _origin is used to switch between lighter fieldsets (add form) and full form (edit form)
    fieldsets_with_inlines = fieldsets_with_inlines_original

    add_fieldsets = [
        (
            "Données C1 (ou ESAT ou SEP)",
            {
                "fields": (
                    "name",
                    "slug",
                    "brand",
                    "siret",
                    "naf",
                    "kind",
                    "nature",
                    "legal_form",  # from API Entreprise mapping
                    "website",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "post_code",
                    "department",
                    "region",
                    "source",
                )
            },
        ),
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "sectors",
                    "networks",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_first_name",
                    "contact_last_name",
                    "contact_email",
                    "contact_phone",
                    "contact_website",
                    "contact_social_website",
                )
            },
        ),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_tender_stats()
        return qs

    def get_readonly_fields(self, request, obj=None):
        """
        Staff can create and edit some Siaes.
        The editable fields are listed in add_fieldsets.
        """
        add_fields = []
        for fieldset in self.add_fieldsets:
            add_fields.extend(list(fieldset[1]["fields"]))
        add_readonly_fields = [field for field in self.readonly_fields if field not in add_fields] + ["slug", "source"]
        # add form
        if not obj:
            return add_readonly_fields
        # also allow edition of some specific Siae
        if obj and obj.source in [siae_constants.SOURCE_STAFF_C4_CREATED, siae_constants.SOURCE_ESAT]:
            return add_readonly_fields + ["name"]
        # for the rest, use the default full-version list
        return self.readonly_fields

    def get_fieldsets(self, request, obj=None):
        """
        The add form has a lighter fieldsets.
        (add_fieldsets is only available for User Admin, so we need to set it manually)
        This method is called every time the form is displayed.
        But the SiaeAdmin instance is loaded when the Django server starts.
        Therefore, the original fieldsets must be reapplied when the edit form is opened after the add form.
        """
        if not obj:
            self.fieldsets_with_inlines = self.add_fieldsets
        else:
            self.fieldsets_with_inlines = self.fieldsets_with_inlines_original  # returns the original fieldsets
        return super().get_fieldsets(request, obj)

    def get_changeform_initial_data(self, request):
        """
        Default values in add form.
        """
        return {"is_active": False, "source": siae_constants.SOURCE_STAFF_C4_CREATED}

    def lookup_allowed(self, lookup, *args, **kwargs):
        if lookup in [
            "tendersiae__email_send_date__isnull",
            "tendersiae__email_link_click_date__isnull",
            "tendersiae__detail_display_date__isnull",
            "tendersiae__detail_contact_click_date__isnull",
            "tendersiae__detail_not_interested_click_date__isnull",
            "tendersiae__source__in",
        ]:
            return True
        return super().lookup_allowed(lookup, *args, **kwargs)

    def save_formset(self, request, form, formset, change):
        """
        Set Note author on create
        """
        for form in formset:
            if type(form.instance) is Note:
                if not form.instance.id and form.instance.text and change:
                    form.instance.author = request.user
        super().save_formset(request, form, formset, change)

    def user_count_with_link(self, siae):
        url = reverse("admin:users_user_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.user_count}</a>')

    user_count_with_link.short_description = User._meta.verbose_name_plural
    user_count_with_link.admin_order_field = "user_count"

    def sector_count_with_link(self, siae):
        url = reverse("admin:sectors_sector_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.sector_count}</a>')

    sector_count_with_link.short_description = "Secteurs"
    sector_count_with_link.admin_order_field = "sector_count"

    def network_count_with_link(self, siae):
        url = reverse("admin:networks_network_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.network_count}</a>')

    network_count_with_link.short_description = Network._meta.verbose_name_plural
    network_count_with_link.admin_order_field = "network_count"

    def group_count_with_link(self, siae):
        url = reverse("admin:siaes_siaegroup_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{siae.group_count}</a>')

    group_count_with_link.short_description = SiaeGroup._meta.verbose_name_plural
    group_count_with_link.admin_order_field = "group_count"

    def activity_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeactivity_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.offer_count}</a>')

    activity_count_with_link.short_description = SiaeActivity._meta.verbose_name_plural
    activity_count_with_link.admin_order_field = "offer_count"

    def offer_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeoffer_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.offer_count}</a>')

    offer_count_with_link.short_description = SiaeOffer._meta.verbose_name_plural
    offer_count_with_link.admin_order_field = "offer_count"

    def label_count_with_link(self, siae):
        url = reverse("admin:siaes_siaelabelold_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.label_count}</a>')

    label_count_with_link.short_description = "Labels"
    label_count_with_link.admin_order_field = "label_count"

    def client_reference_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeclientreference_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.client_reference_count}</a>')

    client_reference_count_with_link.short_description = "Réf. clients"
    client_reference_count_with_link.admin_order_field = "client_reference_count"

    def image_count_with_link(self, siae):
        url = reverse("admin:siaes_siaeimage_changelist") + f"?siae__id__exact={siae.id}"
        return format_html(f'<a href="{url}">{siae.image_count}</a>')

    image_count_with_link.short_description = SiaeImage._meta.verbose_name_plural
    image_count_with_link.admin_order_field = "image_count"

    def coords_display(self, siae):
        if siae.coords:
            return f"{siae.latitude} / {siae.longitude}"
        return "-"

    coords_display.short_description = "Coords (LAT / LNG)"

    def logo_url_display(self, siae):
        if siae.logo_url:
            return mark_safe(
                f'<a href="{siae.logo_url}" target="_blank">'
                f'<img src="{siae.logo_url}" title="{siae.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"

    def import_raw_object_display(self, instance: Siae = None):
        if instance:
            return pretty_print_readonly_jsonfield(instance.import_raw_object)
        return "-"

    import_raw_object_display.short_description = Siae._meta.get_field("import_raw_object").verbose_name

    def tender_count_annotated_with_link(self, siae):
        url = reverse("admin:tenders_tender_changelist") + f"?siaes__in={siae.id}"
        return format_html(f'<a href="{url}">{getattr(siae, "tender_count_annotated", 0)}</a>')

    tender_count_annotated_with_link.short_description = "Besoins concernés"
    tender_count_annotated_with_link.admin_order_field = "tender_count_annotated"

    def tender_email_send_count_annotated_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__email_send_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_email_send_count_annotated", 0)}</a>')

    tender_email_send_count_annotated_with_link.short_description = "Besoins reçus"
    tender_email_send_count_annotated_with_link.admin_order_field = "tender_email_send_count_annotated"

    def tender_email_link_click_count_annotated_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__email_link_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_email_link_click_count_annotated", 0)}</a>')

    tender_email_link_click_count_annotated_with_link.short_description = "Besoins cliqués"
    tender_email_link_click_count_annotated_with_link.admin_order_field = "tender_email_link_click_count_annotated"

    def tender_detail_display_count_annotated_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__detail_display_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_detail_display_count_annotated", 0)}</a>')

    tender_detail_display_count_annotated_with_link.short_description = "Besoins vus"
    tender_detail_display_count_annotated_with_link.admin_order_field = "tender_detail_display_count_annotated"

    def tender_detail_contact_click_count_annotated_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__detail_contact_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_detail_contact_click_count_annotated", 0)}</a>')

    tender_detail_contact_click_count_annotated_with_link.short_description = "Besoins intéressés"
    tender_detail_contact_click_count_annotated_with_link.admin_order_field = (
        "tender_detail_contact_click_count_annotated"
    )

    def tender_detail_not_interested_count_annotated_with_link(self, siae):
        url = (
            reverse("admin:tenders_tender_changelist")
            + f"?siaes__in={siae.id}&tendersiae__detail_not_interested_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(siae, "tender_detail_not_interested_count_annotated", 0)}</a>')

    tender_detail_not_interested_count_annotated_with_link.short_description = "Besoins pas intéressés"
    tender_detail_not_interested_count_annotated_with_link.admin_order_field = (
        "tender_detail_not_interested_count_annotated"
    )

    def recipient_transactional_send_logs_count_with_link(self, obj):
        url = reverse("admin:conversations_templatetransactionalsendlog_changelist") + f"?siae__id__exact={obj.id}"
        return format_html(f'<a href="{url}">{obj.recipient_transactional_send_logs.count()}</a>')

    recipient_transactional_send_logs_count_with_link.short_description = (
        TemplateTransactionalSendLog._meta.verbose_name
    )

    def logs_display(self, siae=None):
        if siae:
            return pretty_print_readonly_jsonfield(siae.logs)
        return "-"

    logs_display.short_description = Siae._meta.get_field("logs").verbose_name

    def extra_data_display(self, instance: Siae = None):
        if instance:
            return pretty_print_readonly_jsonfield(instance.extra_data)
        return "-"

    extra_data_display.short_description = Siae._meta.get_field("extra_data").verbose_name


@admin.register(SiaeUserRequest, site=admin_site)
class SiaeUserRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "siae", "initiator", "assignee", "response", "created_at", "updated_at"]
    search_fields = [
        "id",
        "siae__id",
        "siae__name",
        "initiator__id",
        "initiator__email",
        "assignee__id",
        "assignee__email",
    ]
    search_help_text = (
        "Cherche sur les champs : ID, Structure (ID, Nom), Initiateur (ID, E-mail), Responsable (ID, E-mail)"
    )

    autocomplete_fields = ["siae"]
    readonly_fields = [field.name for field in SiaeUserRequest._meta.fields]
    fields = ["logs_display" if field_name == "logs" else field_name for field_name in readonly_fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def parent_transactional_send_logs_count_with_link(self, obj):
        url = (
            reverse("admin:conversations_templatetransactionalsendlog_changelist")
            + f"?siaeuserrequest__id__exact={obj.id}"
        )
        return format_html(f'<a href="{url}">{obj.parent_transactional_send_logs.count()}</a>')

    parent_transactional_send_logs_count_with_link.short_description = TemplateTransactionalSendLog._meta.verbose_name

    def logs_display(self, siaeuserrequest=None):
        if siaeuserrequest:
            return pretty_print_readonly_jsonfield(siaeuserrequest.logs)
        return "-"

    logs_display.short_description = SiaeUserRequest._meta.get_field("logs").verbose_name


@admin.register(SiaeActivity, site=admin_site)
class SiaeActivityAdmin(admin.ModelAdmin):
    list_display = ["id", "siae_with_link", "created_at", "updated_at"]
    list_filter = ["sectors"]
    search_fields = ["id", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Structure (ID, Nom)"

    autocomplete_fields = ["siae", "sectors", "locations"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Structure",
            {
                "fields": ("siae",),
            },
        ),
        (
            "Prestation",
            {
                "fields": ("sectors", "presta_type"),
            },
        ),
        (
            "Localisation et périmètre d'intervention",
            {
                "fields": ("locations", "geo_range", "geo_range_custom_distance"),
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def siae_with_link(self, siae_offer):
        url = reverse("admin:siaes_siae_change", args=[siae_offer.siae_id])
        return format_html(f'<a href="{url}">{siae_offer.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeOffer, site=admin_site)
class SiaeOfferAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "source", "created_at"]
    list_filter = ["source"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["source", "created_at", "updated_at"]

    def siae_with_link(self, siae_offer):
        url = reverse("admin:siaes_siae_change", args=[siae_offer.siae_id])
        return format_html(f'<a href="{url}">{siae_offer.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeLabelOld, site=admin_site)
class SiaeLabelOldAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["created_at", "updated_at"]

    def siae_with_link(self, siae_label):
        url = reverse("admin:siaes_siae_change", args=[siae_label.siae_id])
        return format_html(f'<a href="{url}">{siae_label.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name
    siae_with_link.admin_order_field = "siae"


@admin.register(SiaeClientReference, site=admin_site)
class SiaeClientReferenceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "logo_url", "logo_url_display", "created_at", "updated_at"]

    def siae_with_link(self, siae_client_reference):
        url = reverse("admin:siaes_siae_change", args=[siae_client_reference.siae_id])
        return format_html(f'<a href="{url}">{siae_client_reference.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name
    siae_with_link.admin_order_field = "siae"

    def logo_url_display(self, siae_client_reference):
        if siae_client_reference.logo_url:
            return mark_safe(
                f'<a href="{siae_client_reference.logo_url}" target="_blank">'
                f'<img src="{siae_client_reference.logo_url}" title="{siae_client_reference.logo_url}" style="max-height:300px" />'  # noqa
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"


@admin.register(SiaeImage, site=admin_site)
class SiaeImageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_with_link", "created_at"]
    search_fields = ["id", "name", "siae__id", "siae__name"]
    search_help_text = "Cherche sur les champs : ID, Nom, Structure (ID, Nom)"

    autocomplete_fields = ["siae"]
    readonly_fields = ["image_name", "image_url", "image_url_display", "created_at", "updated_at"]

    def siae_with_link(self, siae_image):
        url = reverse("admin:siaes_siae_change", args=[siae_image.siae_id])
        return format_html(f'<a href="{url}">{siae_image.siae}</a>')

    siae_with_link.short_description = Siae._meta.verbose_name
    siae_with_link.admin_order_field = "siae"

    def image_url_display(self, siae_image):
        if siae_image.image_url:
            return mark_safe(
                f'<a href="{siae_image.image_url}" target="_blank">'
                f'<img src="{siae_image.image_url}" title="{siae_image.image_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    image_url_display.short_description = "Image"


@admin.register(SiaeGroup, site=admin_site)
class SiaeGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "siae_count_annotated_with_link", "created_at"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["sectors"]
    readonly_fields = [f"{field}_last_updated" for field in SiaeGroup.TRACK_UPDATE_FIELDS] + [
        "siae_count_annotated_with_link",
        "logo_url_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "siret"),
            },
        ),
        (
            "Détails",
            {
                "fields": (
                    "sectors",
                    "year_constitution",
                    "siae_count",
                    "siae_count_last_updated",
                    "siae_count_annotated_with_link",
                    "employees_insertion_count",
                    "employees_insertion_count_last_updated",
                    "employees_permanent_count",
                    "employees_permanent_count_last_updated",
                    "ca",
                    "ca_last_updated",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_first_name",
                    "contact_last_name",
                    "contact_email",
                    "contact_phone",
                    "contact_website",
                    "contact_social_website",
                )
            },
        ),
        (
            "Logo",
            {
                "fields": (
                    "logo_url",
                    "logo_url_display",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        return qs

    def siae_count_annotated_with_link(self, siae_group):
        url = reverse("admin:siaes_siae_changelist") + f"?groups__in={siae_group.id}"
        return format_html(f'<a href="{url}">{siae_group.siae_count_annotated}</a>')

    siae_count_annotated_with_link.short_description = "Nombre de structures (live)"
    siae_count_annotated_with_link.admin_order_field = "siae_count_annotated"

    def logo_url_display(self, siae_group):
        if siae_group.logo_url:
            return mark_safe(
                f'<a href="{siae_group.logo_url}" target="_blank">'
                f'<img src="{siae_group.logo_url}" title="{siae_group.logo_url}" style="max-height:300px" />'
                f"</a>"
            )
        return mark_safe("<div>-</div>")

    logo_url_display.short_description = "Logo"
