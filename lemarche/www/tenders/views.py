from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, ListView, View
from formtools.wizard.views import SessionWizardView

from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.models import User
from lemarche.www.dashboard.mixins import NotSiaeUserRequiredMixin, TenderOwnerRequiredMixin
from lemarche.www.tenders.forms import AddTenderForm, AddTenderStep1Form, AddTenderStep2Form, AddTenderStep3Form
from lemarche.www.tenders.tasks import (  # , send_tender_emails_to_siaes
    notify_admin_tender_created,
    send_siae_interested_email_to_author,
)


TITLE_DETAIL_PAGE_SIAE = "Trouver de nouvelles opportunités"
TITLE_DETAIL_PAGE_OTHERS = "Mes besoins"
TITLE_KIND_SOURCING_SIAE = "Consultation en vue d’un achat"


class TenderCreateMultiStepView(NotSiaeUserRequiredMixin, SessionWizardView):

    STEP_GENERAL = "general"
    STEP_CONTACT = "contact"
    STEP_DESCRIPTION = "description"
    STEP_CONFIRMATION = "confirmation"

    form_list = [
        (STEP_GENERAL, AddTenderStep1Form),
        (STEP_CONTACT, AddTenderStep2Form),
        (STEP_DESCRIPTION, AddTenderStep3Form),
        (STEP_CONFIRMATION, AddTenderForm),
    ]

    TEMPLATES = {
        STEP_GENERAL: "tenders/create_step_1.html",
        STEP_CONTACT: "tenders/create_step_2.html",
        STEP_DESCRIPTION: "tenders/create_step_3.html",
        STEP_CONFIRMATION: "tenders/create_step_4.html",
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})

        if step == self.STEP_CONTACT:
            # import ipdb

            # ipdb.set_trace()
            user = self.request.user
            initial.update(
                {
                    self.STEP_CONTACT: {
                        "contact_first_name": user.first_name,
                        "contact_last_name": user.last_name,
                        "contact_email": user.email,
                        "contact_phone": user.phone,
                    }
                }
            )
        elif step == self.STEP_CONFIRMATION:
            import ipdb

            ipdb.set_trace()
            return {form.cleaned_data for form in self.form_list}
        return initial

    def done(self, form_list, form_dict, **kwargs):
        return render(
            self.request,
            "tenders/multistep_done.html",
            {
                "form_data": [form.cleaned_data for form in form_list],
            },
        )


class TenderCreateView(NotSiaeUserRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "tenders/create.html"
    form_class = AddTenderForm
    context_object_name = "tender"
    success_message = """
        Votre besoin <strong>{}</strong> est déposé sur le marché et les structures
        correspondants à vos critères seront notifiés dès la validation de votre besoin.
    """
    success_url = reverse_lazy("tenders:list")

    def form_valid(self, form):
        tender = form.save(commit=False)
        tender.author = self.request.user
        # we need to save before because the matching of Siaes needs
        # the sectors and perimeters of tender (relation ManyToMany)
        if tender.is_country_area:
            form.cleaned_data.pop("perimeters")
        tender.save()
        form.save_m2m()

        # task to send tender was made in django admin task
        notify_admin_tender_created(tender)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data, tender),
        )
        return HttpResponseRedirect(self.success_url)

    def get_initial(self):
        user = self.request.user
        return {
            "contact_first_name": user.first_name,
            "contact_last_name": user.last_name,
            "contact_email": user.email,
            "contact_phone": user.phone,
        }

    def get_success_message(self, cleaned_data, tender):
        return mark_safe(self.success_message.format(tender.title))


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
        context["kind_title"] = (
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
