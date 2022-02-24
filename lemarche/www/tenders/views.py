from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView

from lemarche.www.tenders.forms import AddTenderForm


class AddTenderView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "tenders/add_tender_form.html"
    form_class = AddTenderForm
    context_object_name = "tender"
    # success_message = "La structure a été ajoutée à votre liste d'achat."
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        tender = form.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data, tender),
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        return super().get_success_url()

    def get_success_message(self, cleaned_data, tender):
        return mark_safe(f"<strong>{tender}</strong> a été ajoutée à ")
