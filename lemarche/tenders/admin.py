import logging

from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django_admin_filters import MultiChoice
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from lemarche.conversations.models import TemplateTransactionalSendLog
from lemarche.notes.models import Note
from lemarche.perimeters.admin import PerimeterRegionFilter
from lemarche.perimeters.models import Perimeter
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.enums import TenderSourcesChoices
from lemarche.tenders.forms import TenderAdminForm
from lemarche.tenders.models import (
    PartnerShareTender,
    QuestionAnswer,
    SuggestedQuestion,
    Tender,
    TenderInstruction,
    TenderQuestion,
    TenderSiae,
    TenderStepsData,
)
from lemarche.users import constants as user_constants
from lemarche.users.models import User
from lemarche.utils.admin.admin_site import admin_site
from lemarche.utils.admin.inline_fieldset import FieldsetsInlineMixin
from lemarche.utils.apis import api_brevo
from lemarche.utils.fields import ChoiceArrayField, pretty_print_readonly_jsonfield
from lemarche.www.tenders.tasks import (
    restart_send_tender_task,
    send_tender_author_modification_request,
    send_tender_author_reject_message,
)


logger = logging.getLogger(__name__)


class KindFilter(MultiChoice):
    FILTER_LABEL = Tender._meta.get_field("kind").verbose_name
    BUTTON_LABEL = "Appliquer"


class ScaleMarcheUselessFilter(MultiChoice):
    FILTER_LABEL = Tender._meta.get_field("scale_marche_useless").verbose_name
    BUTTON_LABEL = "Appliquer"


class SourceFilter(MultiChoice):
    FILTER_LABEL = Tender._meta.get_field("source").verbose_name
    BUTTON_LABEL = "Appliquer"


class HasAmountFilter(admin.SimpleListFilter):
    title = "Montant renseigné ?"
    parameter_name = "has_amount"

    def lookups(self, request, model_admin):
        return (("Yes", "Oui"), ("No", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.has_amount()
        elif value == "No":
            return queryset.filter(amount__isnull=True, amount_exact__isnull=True)
        return queryset


class TallyFilter(admin.SimpleListFilter):
    title = "Source TALLY / Pro"
    parameter_name = "source"

    def lookups(self, request, model_admin):
        return (("TALLY", "Tally"), ("PRO", "Pro"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "TALLY":
            return queryset.filter(source=TenderSourcesChoices.SOURCE_TALLY)
        elif value == "PRO":
            return queryset.exclude(source=TenderSourcesChoices.SOURCE_TALLY)
        return queryset


class AmountCustomFilter(admin.SimpleListFilter):
    title = "Montant du besoin"
    parameter_name = "amount"

    def lookups(self, request, model_admin):
        return (
            ("<10k", "Inférieur (<) à 10k €"),
            ("5k-10k", "Entre (>=) 5k et (<) 10k €"),
            (">=10k", "Supérieur (>=) à 10k €"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        amount_5k = 5 * 10**3
        amount_10k = 10 * 10**3
        if value == "<10k":
            return queryset.filter_by_amount_exact(amount_10k, operation="lt")
        elif value == "5k-10k":
            return queryset.filter_by_amount_exact(amount_5k, operation="gte").filter_by_amount_exact(
                amount_10k, operation="lt"
            )
        elif value == ">=10k":
            return queryset.filter_by_amount_exact(amount_10k, operation="gte")


class ResponseKindFilter(admin.SimpleListFilter):
    title = Tender._meta.get_field("response_kind").verbose_name
    parameter_name = "response_kind"

    def lookups(self, request, model_admin):
        return tender_constants.RESPONSE_KIND_CHOICES

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            queryset = queryset.filter(response_kind__contains=[lookup_value])
        return queryset


class AuthorKindFilter(admin.SimpleListFilter):
    title = "Type du client"
    parameter_name = "author__kind"

    def lookups(self, request, model_admin):
        return user_constants.KIND_CHOICES_WITH_ADMIN

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            queryset = queryset.filter(author__kind=lookup_value)
        return queryset


class UserAdminFilter(admin.SimpleListFilter):
    title = "Suivi bizdev"
    parameter_name = "admins"

    def lookups(self, request, model_admin):
        admins = User.objects.is_admin_bizdev().values("id", "first_name")
        admins_choices = [(admin["id"], admin["first_name"]) for admin in admins]
        admins_choices += [("None", "Sans bizdev")]
        return admins_choices

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            if lookup_value == "None":
                queryset = queryset.filter(admins__isnull=True)
            else:
                queryset = queryset.filter(admins__id__exact=lookup_value)
        return queryset


class TenderNoteInline(GenericTabularInline):
    model = Note
    fields = ["text", "author", "created_at", "updated_at"]
    readonly_fields = ["author", "created_at", "updated_at"]
    extra = 1

    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget(config_name="admin_note_text")},
    }


class TenderQuestionInline(admin.TabularInline):
    model = TenderQuestion
    fields = ["text", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]
    extra = 0


class TenderSiaeInterestedInline(admin.TabularInline):
    model = TenderSiae
    verbose_name = "Structure intéressée"
    verbose_name_plural = "Structures intéressées"
    fields = [
        "id",
        "siae",
        "source",
        "found_with_ai",
        "detail_contact_click_date",
        "survey_transactioned_send_date",
        "survey_transactioned_answer",
        "transactioned",
    ]
    readonly_fields = [field.name for field in TenderSiae._meta.fields if field.name not in ["transactioned"]]
    show_change_link = True
    can_delete = False
    extra = 0
    classes = ["collapse"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(detail_contact_click_date__isnull=False)
        return qs


class TenderSiaeUserInline(admin.TabularInline):
    model = TenderSiae
    fields = [
        "id",
        "user_full_name",
        "user_phone",
        "user",
        "siae",
    ]
    readonly_fields = [field.name for field in TenderSiae._meta.fields if field.name not in ["transactioned"]] + [
        "user_full_name",
        "user_phone",
    ]
    show_change_link = True
    can_delete = False
    extra = 0
    classes = ["collapse"]

    def has_add_permission(self, request, obj=None):
        return False

    def user_full_name(self, obj):
        return obj.user.full_name

    user_full_name.admin_order_field = "user_full_name"
    user_full_name.short_description = "Prénom Nom"

    def user_phone(self, obj):
        return obj.user.phone

    user_phone.admin_order_field = "user_phone"
    user_phone.short_description = User._meta.get_field("phone").verbose_name

    class Meta:
        abstract = True


class TenderSiaeUserSeenButNotYetInterestedInline(TenderSiaeUserInline):
    model = TenderSiae
    verbose_name = "Utilisateur vu"
    verbose_name_plural = "Utilisateurs vus"

    def get_fields(self, request, obj=None):
        return self.fields + ["email_link_click_date", "detail_display_date"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = (
            qs.filter(user__isnull=False)
            .filter(Q(email_link_click_date__isnull=False) | Q(detail_display_date__isnull=False))
            .filter(
                detail_contact_click_date__isnull=True,
                detail_not_interested_click_date__isnull=True,
            )
        )
        return qs


class TenderSiaeUserInterestedInline(TenderSiaeUserInline):
    verbose_name = "Utilisateur intéressé"
    verbose_name_plural = "Utilisateurs intéressés"

    def get_fields(self, request, obj=None):
        return self.fields + ["detail_contact_click_date"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(user__isnull=False, detail_contact_click_date__isnull=False)
        return qs


class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = "__all__"

    is_followed_by_us = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label=Tender._meta.get_field("is_followed_by_us").verbose_name,
    )
    proj_resulted_in_reserved_tender = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label=Tender._meta.get_field("proj_resulted_in_reserved_tender").verbose_name,
    )

    is_reserved_tender = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label=Tender._meta.get_field("is_reserved_tender").verbose_name,
    )

    def clean(self):
        """
        Add validation on form rules:
        - if distance_location is set, then location must be filled + a city
        """
        cleaned_data = super().clean()
        distance_location = cleaned_data.get("distance_location")

        if distance_location:
            location = cleaned_data.get("location")
            if not location:
                raise ValidationError(
                    {"location": "Le champ 'Distance en km' est spécifié, ce champ doit donc être rempli"}
                )
            if location.kind != Perimeter.KIND_CITY:
                raise ValidationError(
                    {"location": "Le champ 'Distance en km' est spécifié, ce champ doit être une ville"}
                )


@admin.register(Tender, site=admin_site)
class TenderAdmin(FieldsetsInlineMixin, admin.ModelAdmin):
    list_display = [
        "title_with_link",
        "kind",
        "amount_display",
        "location_in_list",
        "start_working_date_in_list",
        "siae_count_annotated_with_link_in_list",
        "siae_detail_contact_click_count_annotated_with_link_in_list",
        "status",
        "created_at",
        "is_validated_or_sent",
    ]

    list_filter = [
        TallyFilter,
        AmountCustomFilter,
        ("kind", KindFilter),
        "email_sent_for_modification",
        "is_followed_by_us",
        AuthorKindFilter,
        "status",
        ("scale_marche_useless", ScaleMarcheUselessFilter),
        ("source", SourceFilter),
        HasAmountFilter,
        "deadline_date",
        "start_working_date",
        "created_at",
        ResponseKindFilter,
        "siae_transactioned",
        UserAdminFilter,
    ]
    advanced_filter_fields = (
        "kind",
        "status",
        "scale_marche_useless",
        "deadline_date",
        "start_working_date",
    )
    # filter on "perimeters"? (loads ALL the perimeters... Use django-admin-autocomplete-filter instead?)
    search_fields = ["id", "title", "slug", "author__id", "author__email", "contact_phone"]
    search_help_text = "Cherche sur les champs : ID, Titre, Slug, Auteur (ID, E-mail), Contact Phone"
    ordering = ["-created_at"]

    form = TenderForm
    autocomplete_fields = ["sectors", "location", "perimeters", "author", "admins"]
    readonly_fields = [field for field in Tender.READONLY_FIELDS] + [
        # slug
        # status
        "question_count_with_link",
        "answer_count_with_link",
        "author_kind_detail",
        "is_partner_approch",
        "partner_approch_id",
        "siae_count_annotated_with_link",
        "siae_email_send_count_annotated_with_link",
        "siae_detail_contact_click_count_annotated_with_link",
        "siae_detail_not_interested_click_count_annotated_with_link",
        "siae_transactioned_source",
        "siae_transactioned_last_updated",
        "source",
        "parent_transactional_send_logs_count_with_link",
        "brevo_deal_id",
        "extra_data_display",
        "import_raw_object_display",
        "logs_display",
    ]
    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget},
        ChoiceArrayField: {"widget": forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox-select-multiple"})},
    }

    fieldsets_with_inlines = [
        (
            None,
            {
                "fields": ("title", "slug", "kind", "attachment_one", "attachment_two", "attachment_three"),
            },
        ),
        TenderNoteInline,
        (
            "Détails",
            {
                "fields": (
                    "description",
                    "constraints_title",
                    "constraints",
                    "external_link",
                    "question_count_with_link",
                    "answer_count_with_link",
                ),
            },
        ),
        TenderQuestionInline,
        ("Paramètres d'envois", {"fields": ("limit_send_to_siae_batch", "limit_nb_siae_interested")}),
        (
            "Filtres",
            {
                "fields": (
                    "siae_kind",
                    "sectors",
                    "presta_type",
                )
            },
        ),
        (
            "Lieux d'exécution 'France entière'",
            {
                "fields": ("is_country_area",),
            },
        ),
        (
            "Lieux d'exécution 'spécifique'",
            {
                "fields": (
                    "location",
                    "perimeters",
                    "distance_location",
                    "include_country_area",
                ),
            },
        ),
        (
            "Montant",
            {
                "fields": (
                    "amount",
                    "why_amount_is_blank",
                    "accept_share_amount",
                    "amount_exact",
                    "incremental_custom",
                ),
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "deadline_date",
                    "start_working_date",
                ),
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "author",
                    "author_kind_detail",
                    "contact_first_name",
                    "contact_last_name",
                    "contact_company_name",
                    "contact_email",
                    "contact_phone",
                    "response_kind",
                    "response_is_anonymous",
                    "contact_notifications_disabled",
                ),
            },
        ),
        ("Partenaire APProch", {"classes": ["collapse"], "fields": ("is_partner_approch", "partner_approch_id")}),
        (
            "Structures",
            {
                "fields": (
                    "siae_count_annotated_with_link",
                    "siae_email_send_count_annotated_with_link",
                    "siae_detail_contact_click_count_annotated_with_link",
                    "siae_detail_not_interested_click_count_annotated_with_link",
                )
            },
        ),
        TenderSiaeUserSeenButNotYetInterestedInline,
        TenderSiaeInterestedInline,
        TenderSiaeUserInterestedInline,
        (
            "Transaction ?",
            {
                "fields": (
                    *Tender.FIELDS_SURVEY_TRANSACTIONED,
                    "siae_transactioned",
                    "siae_transactioned_source",
                    "siae_transactioned_last_updated",
                )
            },
        ),
        (
            "Utilité du marché de l'inclusion",
            {"fields": ("scale_marche_useless", "le_marche_doesnt_exist_how_to_find_siae")},
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "published_at",
                    "validated_at",
                    "first_sent_at",
                )
            },
        ),
        (
            "Suivi",
            {
                "fields": (
                    "admins",
                    "is_followed_by_us",
                    "proj_resulted_in_reserved_tender",
                    "is_reserved_tender",
                    "proj_link_to_tender",
                )
            },
        ),
        (
            "Stats",
            {
                "classes": ["collapse"],
                "fields": (
                    "siae_list_last_seen_date",
                    "source",
                    "parent_transactional_send_logs_count_with_link",
                    "brevo_deal_id",
                    "extra_data_display",
                ),
            },
        ),
        ("Si importé", {"classes": ["collapse"], "fields": ("import_raw_object_display",)}),
        ("Logs", {"classes": ["collapse"], "fields": ("logs_display",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    ]

    change_form_template = "tenders/admin_change_form.html"

    class Media:
        js = ["/static/js/admin_tender_confirmation.js"]

    def _handle_email_sent_for_modification(self, request, obj):
        """
        Send an email to the author and set some fields with 'set_modification_request'
        Display an error message if the email can't be sent
        """
        try:
            send_tender_author_modification_request(tender=obj)
            obj.set_modification_request()
            self.message_user(request, "Une demande de modification a été envoyée à l'auteur du besoin")
        except Exception as e:
            self.message_user(
                request,
                "Erreur lors de l'envoi de la demande de modification : veuillez contacter le support.",
                level="error",
            )
            logger.error(f"Exception when sending mail {e}")
        finally:
            return HttpResponseRedirect(".")

    def handle_rejected_status(self, request, obj):
        """
        If tender status is REJECTED, send an email to the author and redirect to the same page.
        """
        send_tender_author_reject_message(tender=obj)
        self.message_user(request, "Un email de rejet a été envoyé à l'auteur du besoin")
        return HttpResponseRedirect(".")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("author", "location")
        qs = qs.with_siae_stats()
        # qs = qs.with_question_stats()  # doesn't work when chaining these 2 querysets: adds duplicates...
        return qs

    def get_changeform_initial_data(self, request):
        """
        Default values in add form.
        """
        return {"source": TenderSourcesChoices.SOURCE_STAFF_C4_CREATED}

    def lookup_allowed(self, lookup, *args, **kwargs):
        if lookup in [
            "tendersiae__email_send_date__isnull",
            "tendersiae__email_link_click_date__isnull",
            "tendersiae__detail_display_date__isnull",
            "tendersiae__detail_contact_click_date__isnull",
            "tendersiae__detail_not_interested_click_date__isnull",
            "author__company_id__exact",
        ]:
            return True
        return super().lookup_allowed(lookup, *args, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:
            # add status in read only when the tender is not owned by the current user
            if obj.author_id and obj.author_id != request.user.id:
                readonly_fields.append("status")
            # slug cannot be changed once the tender is validated
            if obj.status == Tender.StatusChoices.STATUS_VALIDATED:
                readonly_fields.append("slug")
        return readonly_fields

    def save_model(self, request, obj: Tender, form, change):
        """
        Set Tender author on create
        """
        if not obj.id and not obj.author_id:
            obj.author = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        """
        Set Note author on create
        """
        for form in formset:
            if type(form.instance) is Note:
                if not form.instance.id and form.instance.text and change:
                    form.instance.author = request.user
        super().save_formset(request, form, formset, change)

    def is_validated_or_sent(self, tender: Tender):
        return tender.is_validated_or_sent

    is_validated_or_sent.boolean = True
    is_validated_or_sent.short_description = "Valider"

    def question_count_with_link(self, tender):
        url = reverse("admin:tenders_tenderquestion_changelist") + f"?tender__in={tender.id}"
        return format_html(f'<a href="{url}">{tender.questions.count()}</a>')

    question_count_with_link.short_description = TenderQuestion._meta.verbose_name_plural

    def answer_count_with_link(self, tender):
        answers = QuestionAnswer.objects.filter(question__tender=tender)
        id_list = [str(answer.id) for answer in answers]
        id_string = ",".join(id_list)
        url = reverse("admin:tenders_questionanswer_changelist") + f"?id__in={id_string}"
        return format_html(f'<a href="{url}">{answers.count()}</a>')

    answer_count_with_link.short_description = QuestionAnswer._meta.verbose_name_plural

    def title_with_link(self, tender):
        url = reverse("admin:tenders_tender_change", args=[tender.id])
        return format_html(f'<a href="{url}">{tender.title}</a>')

    title_with_link.short_description = "Titre du besoin"
    title_with_link.admin_order_field = "title"

    def amount_display(self, tender):
        return tender.amount_admin_display

    amount_display.short_description = "Budget"
    amount_display.admin_order_field = "amount_exact"

    def location_in_list(self, tender):
        return tender.location

    location_in_list.short_description = "Lieu d'inter"
    location_in_list.admin_order_field = "location"

    def start_working_date_in_list(self, tender):
        return tender.start_working_date

    start_working_date_in_list.short_description = "Début"
    start_working_date_in_list.admin_order_field = "start_working_date"

    def author_kind_detail(self, tender):
        return tender.author.kind_detail_display

    author_kind_detail.short_description = "Type du client"
    author_kind_detail.admin_order_field = "author__kind"

    def is_partner_approch(self, tender: Tender):
        return tender.is_partner_approch

    is_partner_approch.boolean = True
    is_partner_approch.short_description = "Partenaire APProch ?"

    def siae_count_annotated_with_link(self, tender):
        url = reverse("admin:siaes_siae_changelist") + f"?tenders__in={tender.id}&tendersiae__source__in="
        url += ",".join(tender_constants.TENDER_SIAE_SOURCES_EXCEPT_IA)
        return format_html(f'<a href="{url}">{getattr(tender, "siae_count_annotated", 0)}</a>')

    siae_count_annotated_with_link.short_description = "S. concernées"

    def siae_count_annotated_with_link_in_list(self, tender):
        return self.siae_count_annotated_with_link(tender)

    siae_count_annotated_with_link_in_list.short_description = "S. concer."
    siae_count_annotated_with_link_in_list.admin_order_field = "siae_count_annotated"

    def siae_email_send_count_annotated_with_link(self, tender):
        url = (
            reverse("admin:siaes_siae_changelist")
            + f"?tenders__in={tender.id}&tendersiae__email_send_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(tender, "siae_email_send_count_annotated", 0)}</a>')

    siae_email_send_count_annotated_with_link.short_description = "S. contactées"
    siae_email_send_count_annotated_with_link.admin_order_field = "siae_email_send_count_annotated"

    def siae_detail_contact_click_count_annotated_with_link(self, tender):
        url = (
            reverse("admin:siaes_siae_changelist")
            + f"?tenders__in={tender.id}&tendersiae__detail_contact_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(tender, "siae_detail_contact_click_count_annotated", 0)}</a>')

    siae_detail_contact_click_count_annotated_with_link.short_description = "S. intéressées"

    def siae_detail_contact_click_count_annotated_with_link_in_list(self, tender):
        return self.siae_detail_contact_click_count_annotated_with_link(tender)

    siae_detail_contact_click_count_annotated_with_link_in_list.short_description = "S. intér."
    siae_detail_contact_click_count_annotated_with_link_in_list.admin_order_field = (
        "siae_detail_contact_click_count_annotated"
    )

    def siae_detail_not_interested_click_count_annotated_with_link(self, tender):
        url = (
            reverse("admin:siaes_siae_changelist")
            + f"?tenders__in={tender.id}&tendersiae__detail_not_interested_click_date__isnull=False"
        )
        return format_html(
            f'<a href="{url}">{getattr(tender, "siae_detail_not_interested_click_count_annotated", 0)}</a>'
        )

    siae_detail_not_interested_click_count_annotated_with_link.short_description = "S. pas intéressées"
    siae_detail_not_interested_click_count_annotated_with_link.admin_order_field = (
        "siae_detail_not_interested_click_count_annotated"
    )

    def parent_transactional_send_logs_count_with_link(self, obj):
        url = reverse("admin:conversations_templatetransactionalsendlog_changelist") + f"?tender__id__exact={obj.id}"
        return format_html(f'<a href="{url}">{obj.parent_transactional_send_logs.count()}</a>')

    parent_transactional_send_logs_count_with_link.short_description = TemplateTransactionalSendLog._meta.verbose_name

    def logs_display(self, tender=None):
        if tender:
            return pretty_print_readonly_jsonfield(tender.logs)
        return "-"

    logs_display.short_description = Tender._meta.get_field("logs").verbose_name

    def response_change(self, request, obj: Tender):
        """
        Catch submit of custom admin button to Validate or Resend Tender
        """
        # Delegate handling of each custom action to dedicated methods
        action_handlers = [
            ("_calculate_tender", self._handle_calculate_tender),
            ("_validate_send_to_siaes", self._handle_validate_send_to_siaes),
            ("_validate_send_to_commercial_partners", self._handle_validate_send_to_commercial_partners),
            ("_send_modification_request", self._handle_email_sent_for_modification),
            ("_reject_tender", self._handle_reject_tender),
            ("_restart_tender", self._handle_restart_tender),
        ]

        for action_key, handler in action_handlers:
            if request.POST.get(action_key):
                return handler(request, obj)

        return super().response_change(request, obj)

    def _handle_calculate_tender(self, request, obj: Tender):
        """Handle calculate tender button action."""
        obj.set_siae_found_list()
        self.message_user(request, "Les structures concernées ont été mises à jour.")
        # redirect to structures sections
        return HttpResponseRedirect(request.path + "#structures")

    def _handle_validate_send_to_siaes(self, request, obj: Tender):
        """Handle validation and send to SIAEs action."""
        # Check if sectors are filled before validating
        if obj.sectors.count() == 0:
            self.message_user(
                request,
                "Erreur : Les secteurs d'activité doivent être renseignés avant de valider le besoin.",
                level="ERROR",
            )
            # redirect to change page and force scroll to top (override any "#structures" fragment)
            return HttpResponseRedirect(request.path + "#")
        obj.set_validated()
        if obj.is_followed_by_us:
            try:
                api_brevo.create_deal(tender=obj, owner_email=request.user.email)
                # we link deal(tender) with author contact
                api_brevo.link_deal_with_contact_list(tender=obj)
                self.message_user(request, "Ce dépôt de besoin a été synchronisé avec Brevo")
            except Exception as e:
                self.message_user(request, f"Erreur dans la synchronisation du DDB avec Brevo {str(e)}")
        self.message_user(request, "Ce dépôt de besoin a été validé. Il sera envoyé en temps voulu :)")
        # redirect to change page and force scroll to top (override any "#structures" fragment)
        return HttpResponseRedirect(request.path + "#")

    def _handle_validate_send_to_commercial_partners(self, request, obj: Tender):
        """Handle validation and send only to commercial partners action."""
        # Check if sectors are filled before validating
        if obj.sectors.count() == 0:
            self.message_user(
                request,
                "Erreur : Les secteurs d'activité doivent être renseignés avant de valider le besoin.",
                level="ERROR",
            )
            # redirect to change page and force scroll to top (override any "#structures" fragment)
            return HttpResponseRedirect(request.path + "#")
        obj.send_to_commercial_partners_only = True
        obj.set_validated()
        # we don't need to send it in the crm, partners manage them
        self.message_user(request, "Ce dépôt de besoin a été validé. Il sera envoyé aux partenaires :)")
        # redirect to change page and force scroll to top (override any "#structures" fragment)
        return HttpResponseRedirect(request.path + "#")

    def _handle_reject_tender(self, request, obj: Tender):
        """Handle reject tender action."""
        obj.set_rejected()
        return self.handle_rejected_status(request, obj)

    def _handle_restart_tender(self, request, obj: Tender):
        """Handle restart tender action."""
        restart_send_tender_task(tender=obj)
        self.message_user(request, "Ce dépôt de besoin a été renvoyé aux structures")
        # redirect to change page and force scroll to top (override any "#structures" fragment)
        return HttpResponseRedirect(request.path + "#")

    def extra_data_display(self, instance: Tender = None):
        if instance:
            return pretty_print_readonly_jsonfield(instance.extra_data)
        return "-"

    extra_data_display.short_description = Tender._meta.get_field("extra_data").verbose_name

    def import_raw_object_display(self, instance: Tender = None):
        if instance:
            return pretty_print_readonly_jsonfield(instance.import_raw_object)
        return "-"

    import_raw_object_display.short_description = Tender._meta.get_field("import_raw_object").verbose_name


@admin.register(TenderQuestion, site=admin_site)
class TenderQuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "tender_with_link", "created_at"]
    search_fields = ["id", "text", "tender__id", "tender__name"]
    search_help_text = "Cherche sur les champs : ID, Texte, Besoin (ID, Titre)"

    autocomplete_fields = ["tender"]
    readonly_fields = ["created_at", "updated_at"]

    def tender_with_link(self, tender_question):
        url = reverse("admin:tenders_tender_change", args=[tender_question.tender_id])
        return format_html(f'<a href="{url}">{tender_question.tender}</a>')

    tender_with_link.short_description = "Besoin d'achat"
    tender_with_link.admin_order_field = "tender"


@admin.register(QuestionAnswer, site=admin_site)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ["id", "answer", "question", "siae"]
    search_fields = ["id", "answer", "question", "siae"]


@admin.register(SuggestedQuestion, site=admin_site)
class SuggestedQuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "text"]


class PartnerShareTenderNoteInline(GenericTabularInline):
    model = Note
    fields = ["text", "author", "created_at", "updated_at"]
    readonly_fields = ["author", "created_at", "updated_at"]
    extra = 1

    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget(config_name="admin_note_text")},
    }


@admin.register(PartnerShareTender, site=admin_site)
class PartnerShareTenderAdmin(FieldsetsInlineMixin, admin.ModelAdmin, DynamicArrayMixin):
    form = TenderAdminForm
    list_display = ["id", "name", "is_active", "perimeters_string", "amount_in", "created_at"]
    list_filter = ["is_active", PerimeterRegionFilter, "amount_in"]
    search_fields = ["id", "name", "contact_email_list"]
    search_help_text = "Cherche sur les champs : ID, Nom, Contact (E-mail)"

    readonly_fields = ["perimeters_string", "logs_display", "created_at", "updated_at"]
    autocomplete_fields = ["perimeters"]

    fieldsets_with_inlines = [
        (
            None,
            {
                "fields": ("name", "is_active", "perimeters", "amount_in", "contact_email_list"),
            },
        ),
        TenderNoteInline,
        (
            "Stats",
            {
                "fields": ("logs_display",),
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("perimeters")
        return qs

    def save_formset(self, request, form, formset, change):
        """
        Set Note author on create
        """
        for form in formset:
            if type(form.instance) is Note:
                if not form.instance.id and form.instance.text and change:
                    form.instance.author = request.user
        super().save_formset(request, form, formset, change)

    def perimeters_string(self, partnersharetender):
        return partnersharetender.perimeters_list_string

    perimeters_string.short_description = "Périmètres"

    def logs_display(self, partnersharetender=None):
        if partnersharetender:
            return pretty_print_readonly_jsonfield(partnersharetender.logs)
        return "-"

    logs_display.short_description = PartnerShareTender._meta.get_field("logs").verbose_name


@admin.register(TenderStepsData, site=admin_site)
class TenderStepsDataAdmin(admin.ModelAdmin):
    list_display = ["created_at", "updated_at", "uuid"]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "uuid",
        "steps_data_display",
    ]

    def steps_data_display(self, tender_steps_data: TenderStepsData = None):
        if tender_steps_data:
            return pretty_print_readonly_jsonfield(tender_steps_data.steps_data)
        return "-"

    steps_data_display.short_description = "Données saisies dans les étapes"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TenderSiaeSourceFilter(MultiChoice):
    FILTER_LABEL = TenderSiae._meta.get_field("source").verbose_name
    BUTTON_LABEL = "Appliquer"


class TenderSiaeStatusFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return tender_constants.TENDER_SIAE_STATUS_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        else:
            return queryset.filter(status_annotated=value)


@admin.register(TenderSiae, site=admin_site)
class TenderSiaeAdmin(admin.ModelAdmin):
    list_display = ["created_at", "siae_with_app_link", "tender_with_link", "source", "status", "transactioned"]
    list_filter = [
        ("source", TenderSiaeSourceFilter),
        TenderSiaeStatusFilter,
        "survey_transactioned_answer",
        "transactioned",
    ]

    readonly_fields = [field for field in TenderSiae.READONLY_FIELDS] + [
        "siae",
        "siae_with_app_link",
        "tender",
        "tender_with_link",
        "transactioned_source",
        "parent_transactional_send_logs_count_with_link",
        "logs_display",
    ]

    fieldsets = (
        (
            None,
            {"fields": ("siae", "siae_with_app_link", "tender_with_link", "source", "found_with_ai")},
        ),
        ("Mise en relation", {"fields": (*TenderSiae.FIELDS_RELATION, "status")}),
        (
            "Transaction ?",
            {"fields": (*TenderSiae.FIELDS_SURVEY_TRANSACTIONED, "transactioned", "transactioned_source")},
        ),
        ("Utilisateur", {"fields": ("user",)}),
        (
            "Stats",
            {
                "fields": (
                    "parent_transactional_send_logs_count_with_link",
                    "logs_display",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_prefetch_related()
        qs = qs.with_status()
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def siae_with_app_link(self, tendersiae):
        url = reverse("siae:detail", args=[tendersiae.siae.slug])
        return format_html(f'<a href="{url}" target="_blank">{tendersiae.siae.brand} ({tendersiae.siae.name})</a>')

    siae_with_app_link.short_description = "Structure (lien vers l'app)"
    siae_with_app_link.admin_order_field = "siae"

    def tender_with_link(self, tendersiae):
        url = reverse("admin:tenders_tender_change", args=[tendersiae.tender.slug])
        return format_html(f'<a href="{url}">{tendersiae.tender}</a>')

    tender_with_link.short_description = "Besoin d'achat (lien vers l'admin)"
    tender_with_link.admin_order_field = "tender"

    def status(self, tendersiae):
        return tendersiae.status

    status.short_description = "Status"
    status.admin_order_field = "status"

    def parent_transactional_send_logs_count_with_link(self, obj):
        url = (
            reverse("admin:conversations_templatetransactionalsendlog_changelist") + f"?tendersiae__id__exact={obj.id}"
        )
        return format_html(f'<a href="{url}">{obj.parent_transactional_send_logs.count()}</a>')

    parent_transactional_send_logs_count_with_link.short_description = TemplateTransactionalSendLog._meta.verbose_name

    def logs_display(self, tender=None):
        if tender:
            return pretty_print_readonly_jsonfield(tender.logs)
        return "-"

    logs_display.short_description = Tender._meta.get_field("logs").verbose_name


@admin.register(TenderInstruction, site=admin_site)
class TenderInstructionAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "tender_type", "tender_source"]
    search_fields = ["id", "title", "tender_type", "tender_source"]

    formfield_overrides = {
        models.TextField: {"widget": CKEditorWidget},
    }
