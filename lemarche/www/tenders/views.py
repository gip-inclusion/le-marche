from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView, UpdateView
from formtools.wizard.views import SessionWizardView

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.models import User
from lemarche.utils.data import get_choice
from lemarche.www.auth.tasks import send_new_user_password_reset_link
from lemarche.www.dashboard.mixins import TenderOwnerRequiredMixin
from lemarche.www.tenders.forms import (
    AddTenderStepConfirmationForm,
    AddTenderStepContactForm,
    AddTenderStepDescriptionForm,
    AddTenderStepGeneralForm,
    AddTenderStepSurveyForm,
)
from lemarche.www.tenders.tasks import (  # , send_tender_emails_to_siaes
    notify_admin_tender_created,
    send_siae_interested_email_to_author,
)


TITLE_DETAIL_PAGE_SIAE = "Trouver de nouvelles opportunités"
TITLE_DETAIL_PAGE_OTHERS = "Mes besoins"
TITLE_KIND_SOURCING_SIAE = "Consultation en vue d'un achat"


def create_user_from_anonymous_content(tender_dict: dict) -> User:
    user, created = User.objects.get_or_create(
        email=tender_dict["contact_email"],
        defaults={
            "first_name": tender_dict["contact_first_name"],
            "last_name": tender_dict["contact_last_name"],
            "phone": tender_dict["contact_phone"],
            "company_name": tender_dict["contact_company_name"],
            "kind": User.KIND_BUYER,  # not necessarily true, could be a PARTNER
            "source": User.SOURCE_TENDER_FORM,
        },
    )
    if created and settings.BITOUBI_ENV == "prod":
        send_new_user_password_reset_link(user)
    return user


def create_tender_from_dict(tender_dict: dict) -> Tender:
    tender_dict.pop("contact_company_name", None)
    tender_dict.pop("id_location_name", None)
    location = tender_dict.get("location")
    sectors = tender_dict.pop("sectors", [])
    tender = Tender(**tender_dict)
    tender.save()
    if location:
        tender.perimeters.set([location])
    if sectors:
        tender.sectors.set(sectors)
    return tender


class TenderCreateMultiStepView(SessionWizardView):
    """
    Multi-step Tender create form.
    Note: there is also some code in pages/views.py > csrf_failure to manage edge cases
    """

    instance = None
    success_url = reverse_lazy("tenders:list")
    success_message = """
        Votre besoin <strong>{tender_title}</strong> a été publié sur le marché !<br />
        Les prestataires inclusifs qui correspondent à vos critères seront notifiées
        dès que votre besoin sera validé par notre équipe.
    """

    success_message_draft = """
        Votre besoin <strong>{tender_title}</strong> a été enregistré en brouillon.<br />
        Vous pourrez revenir plus tard pour le publier. Vous le retrouverez dans votre tableau de bord.
    """
    STEP_GENERAL = "general"
    STEP_DESCRIPTION = "description"
    STEP_CONTACT = "contact"
    STEP_SURVEY = "survey"
    STEP_CONFIRMATION = "confirmation"

    TEMPLATES = {
        STEP_GENERAL: "tenders/create_step_general.html",
        STEP_DESCRIPTION: "tenders/create_step_description.html",
        STEP_CONTACT: "tenders/create_step_contact.html",
        STEP_SURVEY: "tenders/create_step_survey.html",
        STEP_CONFIRMATION: "tenders/create_step_confirmation.html",
    }

    form_list = [
        (STEP_GENERAL, AddTenderStepGeneralForm),
        (STEP_DESCRIPTION, AddTenderStepDescriptionForm),
        (STEP_CONTACT, AddTenderStepContactForm),
        (STEP_SURVEY, AddTenderStepSurveyForm),
        (STEP_CONFIRMATION, AddTenderStepConfirmationForm),
    ]

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        # needed to display the Tender preview template
        if self.steps.current == self.STEP_CONFIRMATION:
            tender_dict = self.get_all_cleaned_data()
            tender_dict["sectors_list_string"] = ", ".join(tender_dict["sectors"].values_list("name", flat=True))
            tender_dict["get_kind_display"] = get_choice(Tender.TENDER_KIND_CHOICES, tender_dict["kind"])
            tender_dict["get_amount_display"] = get_choice(
                tender_constants.AMOUNT_RANGE_CHOICES, tender_dict["amount"]
            )
            tender_dict["accept_share_amount_display"] = (
                Tender.TENDER_ACCEPT_SHARE_AMOUNT_TRUE
                if tender_dict["accept_share_amount"]
                else Tender.TENDER_ACCEPT_SHARE_AMOUNT_FALSE
            )
            context.update({"tender": tender_dict})
        return context

    def get_form_instance(self, step):
        if "slug" in self.kwargs:
            self.instance = get_object_or_404(Tender, slug=self.kwargs.get("slug"))

        if self.instance is None:
            self.instance = Tender()
        return self.instance

    def get(self, request, *args, **kwargs):
        if "slug" in self.kwargs:
            self.instance = get_object_or_404(Tender, slug=self.kwargs.get("slug"))
            if self.instance.status != tender_constants.STATUS_DRAFT:
                return redirect("tenders:detail", slug=self.instance.slug)

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self, step):
        kwargs = super().get_form_kwargs(step)
        if step == self.STEP_DESCRIPTION:
            kwargs["kind"] = self.get_cleaned_data_for_step(self.STEP_GENERAL).get("kind")
        if step == self.STEP_CONTACT:
            cleaned_data_description = self.get_cleaned_data_for_step(self.STEP_DESCRIPTION)
            kwargs["max_deadline_date"] = cleaned_data_description.get("start_working_date")
            kwargs["external_link"] = cleaned_data_description.get("external_link")
            kwargs["user"] = self.request.user
        return kwargs

    def save_instance_tender(self, tender_dict: dict, form_dict: dict, is_draft: bool):
        tender_status = tender_constants.STATUS_DRAFT if is_draft else tender_constants.STATUS_PUBLISHED
        if self.instance.id:
            # update
            self.instance.status = tender_status
            sectors = None
            for step, model_form in form_dict.items():
                if model_form.has_changed():
                    if step != self.STEP_SURVEY:
                        for attribute in model_form.changed_data:
                            if attribute == "sectors":
                                sectors = tender_dict.get("sectors", None)
                                self.instance.sectors.set(sectors)
                            elif attribute == "location":
                                location = tender_dict.get("location")
                                self.instance.location = location
                                self.instance.perimeters.set([location])
                            else:
                                setattr(self.instance, attribute, tender_dict.get(attribute))
                    elif step == self.STEP_SURVEY:
                        setattr(self.instance, "scale_marche_useless", tender_dict.get("scale_marche_useless"))
                        self.instance.extra_data.update(tender_dict.get("extra_data"))
            self.instance.save()
        else:
            tender_dict |= {"status": tender_status}
            self.instance = create_tender_from_dict(tender_dict)

    def set_or_create_user(self, tender_dict: dict):
        user: User = None
        if not self.request.user.is_authenticated:
            user = create_user_from_anonymous_content(tender_dict)
        else:
            user = self.request.user
            need_to_be_saved = False
            if not user.phone:
                user.phone = tender_dict.get("contact_phone")
                need_to_be_saved = True
            if not user.company_name:
                user.company_name = tender_dict.get("contact_company_name")
                need_to_be_saved = True
            if need_to_be_saved:
                user.save()
        return user

    def done(self, _, form_dict, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        # anonymous user? create user (or get an existing user by email)
        user = self.set_or_create_user(tender_dict=cleaned_data)
        # when it's done we save the tender
        tender_dict = cleaned_data | {"author": user, "source": Tender.SOURCE_FORM}
        is_draft: bool = self.request.POST.get("is_draft", False)
        self.save_instance_tender(tender_dict=tender_dict, form_dict=form_dict, is_draft=is_draft)
        # we notify the admin team
        if settings.BITOUBI_ENV == "prod":
            notify_admin_tender_created(self.instance)
        # validation & siae contacted? in tenders/admin.py
        # success message & response
        messages.add_message(
            self.request,
            messages.INFO if is_draft else messages.SUCCESS,
            self.get_success_message(cleaned_data, self.instance, is_draft=is_draft),
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.request.user.is_authenticated and not self.request.user.kind == User.KIND_SIAE:
            return reverse_lazy("tenders:list")  # super().get_success_url() doesn't work if called from CSRF error
        return reverse_lazy("pages:home")

    def get_success_message(self, cleaned_data, tender, is_draft):
        return mark_safe(
            self.success_message.format(tender_title=tender.title)
            if not is_draft
            else self.success_message_draft.format(tender_title=tender.title)
        )


class TenderListView(LoginRequiredMixin, ListView):
    template_name = "tenders/list.html"
    model = Tender
    context_object_name = "tenders"
    paginate_by = 10
    paginator_class = Paginator
    status = None

    def get_queryset(self):
        """
        - show matching Tenders for Users KIND_SIAE
        - show owned Tenders for other Users
        """
        user = self.request.user
        queryset = Tender.objects.none()
        if user.kind == User.KIND_SIAE and user.siaes:
            # TODO: manage many siaes
            siaes = user.siaes.all()
            if siaes:
                queryset = Tender.objects.filter_with_siaes(siaes)
        else:
            queryset = Tender.objects.by_user(user).with_siae_stats()
            if self.status:
                queryset = queryset.filter(status=self.status)
        return queryset.order_by_deadline_date()

    def get(self, request, status=None, *args, **kwargs):
        """
        Update 'tender_list_last_seen_date'
        """
        user = self.request.user
        self.status = status
        if user.is_authenticated:
            User.objects.filter(id=user.id).update(tender_list_last_seen_date=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_kind = self.request.user.kind if self.request.user.is_authenticated else "anonymous"
        context["page_title"] = TITLE_DETAIL_PAGE_SIAE if user_kind == User.KIND_SIAE else TITLE_DETAIL_PAGE_OTHERS
        context["title_kind_sourcing_siae"] = TITLE_KIND_SOURCING_SIAE
        context["STATUS_DRAFT"] = tender_constants.STATUS_DRAFT
        context["STATUS_PUBLISHED"] = tender_constants.STATUS_PUBLISHED
        context["STATUS_VALIDATED"] = tender_constants.STATUS_VALIDATED
        return context


class TenderDetailView(DetailView):
    model = Tender
    template_name = "tenders/detail.html"
    context_object_name = "tender"

    def get(self, request, *args, **kwargs):
        """
        update 'detail_display_date' (if the User has any Siae linked to this Tender)
        """
        user = self.request.user
        if user.is_authenticated:
            tender: Tender = self.get_object()
            if user.kind == User.KIND_SIAE:
                # user might not be concerned with this tender: we create TenderSiae stats
                if not user.has_tender_siae(tender):
                    for siae in user.siaes.all():
                        TenderSiae.objects.create(tender=tender, siae=siae, source=TenderSiae.TENDER_SIAE_SOURCE_LINK)
                # update stats
                TenderSiae.objects.filter(
                    tender=tender, siae__in=user.siaes.all(), detail_display_date__isnull=True
                ).update(detail_display_date=timezone.now(), updated_at=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tender: Tender = self.get_object()
        user = self.request.user
        user_kind = user.kind if user.is_authenticated else "anonymous"
        context["parent_title"] = TITLE_DETAIL_PAGE_SIAE if user_kind == User.KIND_SIAE else TITLE_DETAIL_PAGE_OTHERS
        context["tender_kind_display"] = (
            TITLE_KIND_SOURCING_SIAE
            if user_kind == User.KIND_SIAE and tender.kind == Tender.TENDER_KIND_PROJECT
            else tender.get_kind_display()
        )
        if user.is_authenticated:
            if tender.author == user:
                context["siae_contact_click_count"] = TenderSiae.objects.filter(
                    tender=tender, contact_click_date__isnull=False
                ).count()
                context["is_draft"] = tender.status == tender_constants.STATUS_DRAFT
            elif user.kind == User.KIND_SIAE:
                context["user_siae_has_contact_click_date"] = TenderSiae.objects.filter(
                    tender=tender, siae__in=user.siaes.all(), contact_click_date__isnull=False
                ).exists()
            elif user.kind == User.KIND_PARTNER:
                context["user_partner_can_display_tender_contact_details"] = user.can_display_tender_contact_details
            else:
                pass

        return context


class TenderDetailContactClickStat(LoginRequiredMixin, UpdateView):
    """
    Endpoint to track contact_clicks by interested Siaes
    We might also send a notification to the buyer
    """

    template_name = "tenders/_contact_click_confirm_modal.html"
    model = Tender

    def get_object(self):
        return get_object_or_404(Tender, slug=self.kwargs.get("slug"))

    def post(self, request, *args, **kwargs):
        user = self.request.user
        contact_click_confirm = self.request.POST.get("contact_click_confirm", False) == "true"
        if user.kind == User.KIND_SIAE:
            if contact_click_confirm:
                # update contact_click_date
                tender = self.get_object()
                TenderSiae.objects.filter(
                    tender=tender, siae__in=user.siaes.all(), contact_click_date__isnull=True
                ).update(contact_click_date=timezone.now(), updated_at=timezone.now())
                # notify the tender author
                send_siae_interested_email_to_author(tender)
                # redirect
                messages.add_message(self.request, messages.SUCCESS, self.get_success_message(contact_click_confirm))
            else:
                messages.add_message(self.request, messages.WARNING, self.get_success_message(contact_click_confirm))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return HttpResponseForbidden()

    def get_success_url(self):
        return reverse_lazy("tenders:detail", args=[self.kwargs.get("slug")])

    def get_success_message(self, contact_click_confirm):
        if contact_click_confirm:
            return "<strong>Bravo !</strong><br />Vos coordonnées, ainsi que le lien vers votre fiche commerciale ont été transmis à l'acheteur. Assurez-vous d'avoir une fiche commerciale bien renseignée."  # noqa
        return "<strong>Répondre à cette opportunité</strong><br />Pour répondre à cette opportunité, vous devez accepter d'être mis en relation avec l'acheteur."  # noqa


class TenderSiaeInterestedListView(TenderOwnerRequiredMixin, ListView):
    queryset = TenderSiae.objects.select_related("tender", "siae").all()
    template_name = "tenders/siae_interested_list.html"
    context_object_name = "tendersiaes"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(tender__slug=self.kwargs.get("slug"), contact_click_date__isnull=False)
        qs = qs.order_by("-contact_click_date")
        return qs

    def get(self, request, *args, **kwargs):
        """
        User should be tender owner : we update siae_interested_list_last_seen_date
        """
        Tender.objects.filter(slug=self.kwargs.get("slug")).update(siae_interested_list_last_seen_date=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tender"] = Tender.objects.get(slug=self.kwargs.get("slug"))
        return context
