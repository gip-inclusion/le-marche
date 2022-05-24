from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView, View
from formtools.wizard.views import SessionWizardView

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.models import User
from lemarche.utils.data import get_choice
from lemarche.www.dashboard.mixins import NotSiaeUserRequiredMixin, TenderOwnerRequiredMixin
from lemarche.www.tenders.forms import (
    AddTenderStepConfirmationForm,
    AddTenderStepContactForm,
    AddTenderStepDescriptionForm,
    AddTenderStepGeneralForm,
)
from lemarche.www.tenders.tasks import (  # , send_tender_emails_to_siaes
    notify_admin_tender_created,
    send_siae_interested_email_to_author,
)


TITLE_DETAIL_PAGE_SIAE = "Trouver de nouvelles opportunités"
TITLE_DETAIL_PAGE_OTHERS = "Mes besoins"
TITLE_KIND_SOURCING_SIAE = "Consultation en vue d’un achat"


def create_tender_from_dict(tender_dict: dict):
    perimeters = tender_dict.pop("perimeters", [])
    sectors = tender_dict.pop("sectors", [])
    tender = Tender(**tender_dict)

    tender.save()
    for perimeter in perimeters:
        tender.perimeters.add(perimeter)
    for sector in sectors:
        tender.sectors.add(sector)
    return tender


class TenderCreateMultiStepView(NotSiaeUserRequiredMixin, SessionWizardView):
    instance = None
    success_url = reverse_lazy("tenders:list")
    success_message = """
        Votre besoin <strong>{tender_title}</strong> a été déposé sur le marché !<br />
        Les {tender_siae_count} structures correspondants à vos critères seront notifiés dès qu'il sera validé par notre équipe.  # noqa
    """

    STEP_GENERAL = "general"
    STEP_DESCRIPTION = "description"
    STEP_CONTACT = "contact"
    STEP_CONFIRMATION = "confirmation"

    TEMPLATES = {
        STEP_GENERAL: "tenders/create_step_general.html",
        STEP_DESCRIPTION: "tenders/create_step_description.html",
        STEP_CONTACT: "tenders/create_step_contact.html",
        STEP_CONFIRMATION: "tenders/create_step_confirmation.html",
    }

    form_list = [
        (STEP_GENERAL, AddTenderStepGeneralForm),
        (STEP_DESCRIPTION, AddTenderStepDescriptionForm),
        (STEP_CONTACT, AddTenderStepContactForm),
        (STEP_CONFIRMATION, AddTenderStepConfirmationForm),
    ]

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        # needed to display the perimeters selected in the previous page
        if self.steps.current == self.STEP_GENERAL:
            if self.get_cleaned_data_for_step(self.STEP_GENERAL):
                tender_perimeters = self.get_cleaned_data_for_step(self.STEP_GENERAL).get("perimeters")
                tender_is_country_area = self.get_cleaned_data_for_step(self.STEP_GENERAL).get("is_country_area")
                if not tender_is_country_area:
                    context["current_perimeters"] = list(tender_perimeters.values("id", "name"))
        # needed to display the Tender preview template
        if self.steps.current == self.STEP_CONFIRMATION:
            tender_dict = self.get_all_cleaned_data()
            tender_dict["get_sectors_names"] = ", ".join(tender_dict["sectors"].values_list("name", flat=True))
            tender_dict["get_perimeters_names"] = ", ".join(tender_dict["perimeters"].values_list("name", flat=True))
            tender_dict["get_kind_display"] = get_choice(Tender.TENDER_KIND_CHOICES, tender_dict["kind"])
            tender_dict["get_amount_display"] = get_choice(
                tender_constants.AMOUNT_RANGE_CHOICES, tender_dict["amount"]
            )
            context.update({"tender": tender_dict})
        return context

    def get_form_instance(self, step):
        if self.instance is None:
            self.instance = Tender()
        if step == self.STEP_CONTACT:
            user = self.request.user
            return Tender(
                **{
                    "contact_first_name": user.first_name,
                    "contact_last_name": user.last_name,
                    "contact_email": user.email,
                    "contact_phone": user.phone,
                }
            )
        return self.instance

    def get_form_kwargs(self, step):
        kwargs = super().get_form_kwargs(step)
        if step == self.STEP_CONTACT:
            kwargs["max_deadline_date"] = self.get_cleaned_data_for_step(self.STEP_DESCRIPTION).get(
                "start_working_date"
            )
            kwargs["external_link"] = self.get_cleaned_data_for_step(self.STEP_DESCRIPTION).get("external_link")
        return kwargs

    def done(self, *args, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        # when it's done we save the tender
        tender = create_tender_from_dict(cleaned_data | {"author": self.request.user})
        # we notify the admin team
        if settings.BITOUBI_ENV == "prod":
            notify_admin_tender_created(tender)
        # validation & siae contacted? in tenders/admin.py
        # success message & response
        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(cleaned_data, tender),
        )
        return HttpResponseRedirect(self.success_url)

    def get_success_message(self, cleaned_data, tender):
        return mark_safe(
            self.success_message.format(tender_title=tender.title, tender_siae_count=tender.siaes.count())
        )


class TenderListView(LoginRequiredMixin, ListView):
    template_name = "tenders/list.html"
    model = Tender
    context_object_name = "tenders"
    paginate_by = 10
    paginator_class = Paginator

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
                queryset = Tender.objects.filter_with_siae(siaes).is_live()
        else:
            queryset = Tender.objects.by_user(user).with_siae_stats()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_kind = self.request.user.kind if self.request.user.is_authenticated else "anonymous"
        context["page_title"] = TITLE_DETAIL_PAGE_SIAE if user_kind == User.KIND_SIAE else TITLE_DETAIL_PAGE_OTHERS
        context["title_kind_sourcing_siae"] = TITLE_KIND_SOURCING_SIAE
        return context


class TenderDetailView(LoginRequiredMixin, DetailView):
    model = Tender
    template_name = "tenders/detail.html"
    context_object_name = "tender"

    def get(self, request, *args, **kwargs):
        """
        Check if the User has any Siae contacted for this Tender. If yes, update 'detail_display_date'
        """
        if self.request.user.kind == User.KIND_SIAE:
            tender = self.get_object()
            TenderSiae.objects.filter(
                tender=tender, siae__in=self.request.user.siaes.all(), detail_display_date__isnull=True
            ).update(detail_display_date=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tender = self.get_object()
        user_kind = self.request.user.kind if self.request.user.is_authenticated else "anonymous"
        context["parent_title"] = TITLE_DETAIL_PAGE_SIAE if user_kind == User.KIND_SIAE else TITLE_DETAIL_PAGE_OTHERS
        context["tender_kind_display"] = (
            TITLE_KIND_SOURCING_SIAE
            if user_kind == User.KIND_SIAE and tender.kind == Tender.TENDER_KIND_PROJECT
            else tender.get_kind_display()
        )
        if self.request.user.kind == User.KIND_SIAE:
            context["user_has_detail_display_date"] = TenderSiae.objects.filter(
                tender=tender, siae__in=self.request.user.siaes.all(), detail_display_date__isnull=False
            ).exists()
            context["user_has_contact_click_date"] = TenderSiae.objects.filter(
                tender=tender, siae__in=self.request.user.siaes.all(), contact_click_date__isnull=False
            ).exists()
        if tender.author == self.request.user:
            context["siae_contact_click_count"] = TenderSiae.objects.filter(
                tender=tender, contact_click_date__isnull=False
            ).count()
        return context


class TenderDetailContactClickStat(LoginRequiredMixin, View):
    """
    Endpoint to track contact_clicks by interested Siaes
    We might also send a notification to the buyer
    """

    def get_object(self):
        return get_object_or_404(Tender, slug=self.kwargs.get("slug"))

    def post(self, request, *args, **kwargs):
        if self.request.user.kind == User.KIND_SIAE:
            # update contact_click_date
            tender = self.get_object()
            TenderSiae.objects.filter(
                tender=tender, siae__in=self.request.user.siaes.all(), contact_click_date__isnull=True
            ).update(contact_click_date=timezone.now())
            send_siae_interested_email_to_author(tender)
            return JsonResponse({"message": "success"})
        else:
            return HttpResponseForbidden()


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
        - if there isn't any Siae interested, redirect
        - user should be tender owner : update siae_interested_list_last_seen_date
        """
        if not self.get_queryset().count():
            return HttpResponseRedirect(reverse_lazy("tenders:list"))
        Tender.objects.filter(slug=self.kwargs.get("slug")).update(siae_interested_list_last_seen_date=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tender"] = context["tendersiaes"].first().tender
        return context
