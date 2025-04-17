import json
import logging

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, TemplateView, View
from django.views.generic.edit import FormMixin
from wagtail.models import Site as WagtailSite

from lemarche.siaes.models import Siae, SiaeGroup
from lemarche.utils.tracker import track
from lemarche.www.pages.forms import (
    CompanyReferenceCalculatorForm,
    ContactForm,
    ImpactCalculatorForm,
    SocialImpactBuyersCalculatorForm,
)
from lemarche.www.pages.tasks import send_contact_form_email, send_contact_form_receipt


logger = logging.getLogger(__name__)


class ContactView(SuccessMessageMixin, FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_message = (
        "Votre message a bien été envoyé, merci ! Notre délai de traitement est en moyenne de 3 jours ouvrés."
    )
    success_url = reverse_lazy("wagtail_serve", args=("",))

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
        - filter using the SiaeFilterForm
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
                context["show_results"] = True
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


def calculate_social_impact_buyers(amount: int):
    AMOUNT_THRESHOLD = 3699
    if amount <= AMOUNT_THRESHOLD:
        return {
            "nb_of_hours_per_mounth": round(amount / 26),
        }
    return {
        "nb_of_jobs_per_mounth": round(amount / 3700),
        "nb_of_jobs_per_year": amount / 3700 / 12,
    }


class SocialImpactBuyersCalculatorView(FormMixin, TemplateView):
    template_name = "pages/social-impact-for-buyers.html"
    form_class = SocialImpactBuyersCalculatorForm
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if len(self.request.GET.keys()):
            self.form = SocialImpactBuyersCalculatorForm(data=self.request.GET)
            context["form"] = self.form
            if self.form.is_valid():
                amount = self.form.cleaned_data.get("amount")
                context["results"] = calculate_social_impact_buyers(amount)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CompanyReferenceCalculatorView(FormMixin, ListView):
    template_name = "pages/company-reference-calculator.html"
    form_class = CompanyReferenceCalculatorForm

    def get_queryset(self):
        """
        Filter results.
        - filter using the SiaeFilterForm
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


def csrf_failure(request, reason=""):  # noqa C901
    """
    Display a custom message on CSRF errors, log failure
    """
    template_name = "403_csrf.html"
    context = {}

    logger.error(
        "CSRF FAILURE REASON %s PATH %s POST %s SESSION %s", reason, request.path, request.POST, dict(request.session)
    )

    return render(request, template_name, context)


def trigger_error(request):
    """Endpoint to send frontend errors to Sentry."""
    if request.POST:
        raise Exception("%s error: %s" % (request.POST.get("status_code"), request.POST.get("error_message")))
    print(1 / 0)  # Should raise a ZeroDivisionError.


class SitemapView(View):
    def get(self, request):
        # Récupérer la page d'accueil
        site = WagtailSite.find_for_request(request)
        homepage = site.root_page  # Page d'accueil de Wagtail

        # Récupérer toutes les pages descendantes publiées
        all_pages = homepage.get_descendants(inclusive=True).live()

        # Construire une liste des URLs et titres
        urls_with_titles = [
            {"url": page.get_full_url(request=request), "title": page.title, "depth": page.depth - homepage.depth}
            for page in all_pages
        ]

        return render(request, "pages/plan_du_site.html", {"sitemap_urls": urls_with_titles})
