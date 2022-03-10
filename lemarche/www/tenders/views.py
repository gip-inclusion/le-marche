from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView

from lemarche.www.tenders.forms import AddTenderForm


class TenderAddView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "tenders/add_tender_form.html"
    form_class = AddTenderForm
    context_object_name = "tender"
    success_message = """
        Votre besoin <strong>{}</strong> est déposé sur le marché et les structures
        correspondants à vos critères seront notifiés
    """
    success_url = reverse_lazy("tenders:list")

    def form_valid(self, form):
        tender = form.save(commit=False)
        tender.author = self.request.user
        tender.save()
        form.save_m2m()
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
