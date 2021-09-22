from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponsePermanentRedirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView

from lemarche.pages.models import Page
from lemarche.www.pages.forms import ContactForm
from lemarche.www.pages.tasks import send_contact_form_email
from lemarche.www.search.forms import SiaeSearchForm


class HomeView(FormView):
    template_name = "pages/home.html"
    form_class = SiaeSearchForm


class ContactView(SuccessMessageMixin, FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_message = "Votre message a bien été envoyé, merci !"
    success_url = reverse_lazy("pages:home")

    def get_initial(self):
        """If the user is logged in, fill the form with the user's basic info."""
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial["first_name"] = self.request.user.first_name
            initial["last_name"] = self.request.user.last_name
            initial["email"] = self.request.user.email
        return initial

    def form_valid(self, form):
        """Send the content of the form via email."""
        response = super().form_valid(form)
        form_dict = form.cleaned_data
        send_contact_form_email(form_dict)
        return response


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
