import json

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponsePermanentRedirect, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.edit import FormMixin

from lemarche.pages.models import Page
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes.models import Siae, SiaeGroup
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.utils.tracker import track
from lemarche.www.pages.forms import CompanyReferenceCalculatorForm, ContactForm, ImpactCalculatorForm
from lemarche.www.pages.tasks import send_contact_form_email, send_contact_form_receipt
from lemarche.www.tenders.tasks import notify_admin_tender_created
from lemarche.www.tenders.views import (
    TenderCreateMultiStepView,
    create_tender_from_dict,
    create_user_from_anonymous_content,
)


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Check if there is any custom message to display."""
        message = request.GET.get("message", None)
        # On newsletter subscription success, users will be redirected to our website + show them a short message
        if message == "newsletter-success":
            messages.add_message(request, messages.INFO, "Merci de votre inscription à notre newsletter !")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        - add SIAE that should appear in the section "à la une"
        """
        context = super().get_context_data(**kwargs)
        context["user_buyer_count"] = User.objects.filter(kind=User.KIND_BUYER).count()
        context["siae_count"] = Siae.objects.is_live().count()
        context["tender_count"] = Tender.objects.validated().count() + 30  # historic number (before form)
        context["siaes_first_page"] = Siae.objects.filter(is_first_page=True)
        return context


class ContactView(SuccessMessageMixin, FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_message = (
        "Votre message a bien été envoyé, merci ! Notre délai de traitement est en moyenne de 3 jours ouvrés."
    )
    success_url = reverse_lazy("pages:home")

    def get_initial(self):
        """If the user is logged in, fill the form with the user's basic info."""
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial["first_name"] = self.request.user.first_name
            initial["last_name"] = self.request.user.last_name
            initial["email"] = self.request.user.email
            initial["kind"] = self.request.user.kind
        initial["siret"] = self.request.GET.get("siret", None)
        return initial

    def form_valid(self, form):
        """
        - send the content of the form via email to our support
        - also send a receipt to some users
        """
        response = super().form_valid(form)
        form_dict = form.cleaned_data
        send_contact_form_email(form_dict)
        if form_dict["kind"] == "SIAE":
            send_contact_form_receipt(form_dict)
        return response


class SiaeGroupListView(ListView):
    template_name = "pages/groupements.html"
    queryset = SiaeGroup.objects.prefetch_related("sectors").all().order_by("name")
    context_object_name = "siaegroups"


class StatsView(TemplateView):
    template_name = "pages/stats.html"

    def get_context_data(self, **kwargs):
        """
        - add iframe data
        """
        context = super().get_context_data(**kwargs)
        context["METABASE_PUBLIC_DASHBOARD_URL"] = settings.METABASE_PUBLIC_DASHBOARD_URL
        return context


class PageView(DetailView):
    context_object_name = "flatpage"
    template_name = "pages/flatpage_template.html"

    def get(self, request, *args, **kwargs):
        url = self.kwargs.get("url")
        if not url.endswith("/"):
            return HttpResponsePermanentRedirect(url + "/")
        return super().get(request, *args, **kwargs)

    def get_object(self):
        url = self.kwargs.get("url")
        if not url.startswith("/"):
            url = "/" + url

        try:
            page = Page.objects.get(url=url)
        except Page.DoesNotExist:
            raise Http404("Page inconnue")

        return page


class TrackView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        track(
            page=data.get("page", ""),
            action=data.get("action", ""),
            meta=data.get("meta", None),
        )
        return JsonResponse({"message": "success"})


class ImpactCalculatorView(FormMixin, ListView):
    template_name = "pages/impact-calculator.html"
    form_class = ImpactCalculatorForm

    def get_queryset(self):
        """
        Filter results.
        - filter using the SiaeSearchForm
        - aggregate on impact values
        """
        self.filter_form = ImpactCalculatorForm(data=self.request.GET)
        results = self.filter_form.filter_queryset()
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if len(self.request.GET.keys()):
            siae_search_form = self.filter_form if self.filter_form else ImpactCalculatorForm(data=self.request.GET)
            context["form"] = self.filter_form
            if siae_search_form.is_valid():
                # results
                context["results"] = self.get_queryset()
                context["results_aggregated"] = self.filter_form.impact_aggregation(context["results"])
                context["current_search_query"] = self.request.GET.urlencode()
                # perimeters
                current_perimeters = siae_search_form.cleaned_data.get("perimeters")
                if current_perimeters:
                    context["current_perimeters"] = list(current_perimeters.values("id", "slug", "name"))
                    current_perimeters_list = list(current_perimeters.order_by("name").values_list("name", flat=True))
                    context["current_perimeters_pretty"] = self.limit_list(current_perimeters_list)
                # sectors
                current_sectors = siae_search_form.cleaned_data.get("sectors")
                if current_sectors:
                    context["current_sectors"] = list(current_sectors.values("id", "slug", "name"))
                    current_sectors_list = list(current_sectors.order_by("name").values_list("name", flat=True))
                    context["current_sectors_pretty"] = self.limit_list(current_sectors_list)
        return context

    def limit_list(self, listing: list, limit: int = 3, with_end_elmt=True, end_position="...", sorted=True):
        if sorted:
            listing.sort()
        if len(listing) > limit:
            listing = listing[:limit]
            if with_end_elmt:
                listing.append(end_position)
        return listing


class CompanyReferenceCalculatorView(FormMixin, ListView):
    template_name = "pages/company-reference-calculator.html"
    form_class = CompanyReferenceCalculatorForm

    def get_queryset(self):
        """
        Filter results.
        - filter using the SiaeSearchForm
        """
        self.filter_form = CompanyReferenceCalculatorForm(data=self.request.GET)
        if len(self.request.GET.keys()):
            results = self.filter_form.filter_queryset()
            return results
        else:  # avoid empty filtering
            return Siae.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_has_filtered"] = False
        if len(self.request.GET.keys()):
            siae_search_form = (
                self.filter_form if self.filter_form else CompanyReferenceCalculatorForm(data=self.request.GET)
            )
            context["form"] = self.filter_form
            if siae_search_form.is_valid():
                context["form_has_filtered"] = True
                context["results"] = self.get_queryset()
                context["current_search_query"] = self.request.GET.urlencode()
        return context

    # not needed for now
    # def get_initial(self):
    #     """If the user is logged in, fill the form with the user's company."""
    #     initial = super().get_initial()
    #     if self.request.user.is_authenticated:
    #         initial["company_client_reference"] = self.request.user.company_name
    #     return initial


def csrf_failure(request, reason=""):  # noqa C901
    """
    Display a custom message on CSRF errors
    *BUT* we skip this error if it comes from the Tender create form
    """
    template_name = "403_csrf.html"
    context = {}  # self.get_context_data()

    print("csrf_failure", "request.path", request.path)
    print("csrf_failure", "request.POST", request.POST)
    print("csrf_failure", "request.session", dict(request.session))

    if "/besoins/ajouter/" in request.path:
        # in some cases, there is no POST data...
        # if (
        #     request.POST.get("tender_create_multi_step_view-current_step")
        #     == TenderCreateMultiStepView.STEP_CONFIRMATION
        # ):

        # create tender_dict
        tender_dict = dict(extra_data={})
        formtools_session_step_data = request.session.get("wizard_tender_create_multi_step_view", {}).get(
            "step_data", {}
        )
        for step in formtools_session_step_data.keys():
            for key in formtools_session_step_data.get(step).keys():
                if not key.startswith(("csrfmiddlewaretoken", "tender_create_multi_step_view")):
                    value = formtools_session_step_data.get(step).get(key)
                    key_cleaned = (
                        key.replace("general-", "")
                        .replace("description-", "")
                        .replace("contact-", "")
                        .replace("survey-", "")
                    )
                    if key_cleaned in [
                        "le_marche_doesnt_exist_how_to_find_siae",
                        "providers_out_of_insertion",
                        "worked_with_inclusif_siae_this_kind_tender",
                        "is_encouraged_by_le_marche",
                    ]:
                        tender_dict["extra_data"] |= {key_cleaned: value[0]}

                    elif key_cleaned not in [
                        "sectors",
                        "perimeters",
                        "presta_type",
                        "response_kind",
                        "is_country_area",
                        "accept_share_amount",
                        "accept_cocontracting",
                    ]:
                        if value[0]:
                            tender_dict[key_cleaned] = value[0]
                    elif key_cleaned in [
                        "is_country_area",
                        "accept_share_amount",
                        "accept_cocontracting",
                    ]:
                        tender_dict[key_cleaned] = value[0] == "on"

                    elif key_cleaned == "sectors":
                        tender_dict[key_cleaned] = Sector.objects.filter(slug__in=value)
                    elif key_cleaned == "perimeters":
                        tender_dict[key_cleaned] = Perimeter.objects.filter(slug__in=value)
                    else:  # presta_type, response_kind, marche_benefits
                        tender_dict[key_cleaned] = list() if value[0] == "" else value

        # get user
        if not request.user.is_authenticated:
            user = create_user_from_anonymous_content(tender_dict)
        else:
            user = request.user
        # create tender
        tender = create_tender_from_dict(tender_dict | {"author": user, "source": Tender.SOURCE_FORM_CSRF})

        if settings.BITOUBI_ENV == "prod":
            notify_admin_tender_created(tender)

        messages.add_message(
            request,
            messages.SUCCESS,
            TenderCreateMultiStepView.get_success_message(
                TenderCreateMultiStepView, tender_dict, tender, is_draft=False
            ),
        )
        return HttpResponseRedirect(TenderCreateMultiStepView.success_url)

    # return HttpResponseForbidden()
    return render(request, template_name, context)


def trigger_error(request):
    """Endpoint to send frontend errors to Sentry."""
    if request.POST:
        raise Exception("%s error: %s" % (request.POST.get("status_code"), request.POST.get("error_message")))
    print(1 / 0)  # Should raise a ZeroDivisionError.
