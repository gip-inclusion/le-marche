import json

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponsePermanentRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from lemarche.pages.models import Page
from lemarche.siaes.models import Siae, SiaeGroup
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.utils.tracker import track
from lemarche.www.pages.forms import ContactForm
from lemarche.www.pages.tasks import send_contact_form_email, send_contact_form_receipt


@method_decorator(cache_page(60 * 60), name="dispatch")  # cache 1 hour
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
        context["siae_count"] = Siae.objects.is_live().count()
        context["user_buyer_count"] = User.objects.filter(kind=User.KIND_BUYER).count()
        context["tender_count"] = Tender.objects.count()
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


def trigger_error(request):
    """Endpoint to send frontend errors to Sentry."""
    if request.POST:
        raise Exception("%s error: %s" % (request.POST.get("status_code"), request.POST.get("error_message")))
    print(1 / 0)  # Should raise a ZeroDivisionError.
