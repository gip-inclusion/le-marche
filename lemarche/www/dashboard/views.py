from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.siaes.models import Siae
from lemarche.www.dashboard.forms import (
    ProfileEditForm,
    SiaeAdoptConfirmForm,
    SiaeClientReferenceFormSet,
    SiaeEditInfoContactForm,
    SiaeEditOfferForm,
    SiaeEditOtherForm,
    SiaeEditPrestaForm,
    SiaeLabelFormSet,
    SiaeOfferFormSet,
    SiaeSearchBySiretForm,
)
from lemarche.www.dashboard.mixins import SiaeOwnerRequiredMixin, SiaeUserRequiredMixin


class DashboardHomeView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/home.html"
    context_object_name = "user"

    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = "dashboard/profile_edit.html"
    success_message = "Votre profil a été mis à jour."
    success_url = reverse_lazy("dashboard:home")

    def get_object(self):
        return self.request.user


class SiaeSearchBySiretView(LoginRequiredMixin, SiaeUserRequiredMixin, FormMixin, ListView):
    form_class = SiaeSearchBySiretForm
    template_name = "dashboard/siae_search_by_siret.html"
    context_object_name = "siaes"

    def get_queryset(self):
        """Filter results."""
        filter_form = SiaeSearchBySiretForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get_context_data(self, **kwargs):
        """
        - initialize the form with the query parameters (only if they are present)
        """
        context = super().get_context_data(**kwargs)
        if len(self.request.GET.keys()):
            context["form"] = SiaeSearchBySiretForm(data=self.request.GET)
        return context


class SiaeAdoptConfirmView(LoginRequiredMixin, SiaeUserRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeAdoptConfirmForm
    template_name = "dashboard/siae_adopt_confirm.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Votre structure a été rajoutée dans votre espace."
    success_url = reverse_lazy("dashboard:home")

    def get(self, request, *args, **kwargs):
        """The Siae should not have any users yet."""
        response = super().get(request, *args, **kwargs)
        if self.object.users.count():
            messages.add_message(
                request, messages.INFO, "La structure a déjà été enregistrée sur le marché par un autre utilisateur."
            )
            return HttpResponseRedirect(reverse_lazy("dashboard:home"))
        return response

    def form_valid(self, form):
        """Add the Siae to the User."""
        self.object.users.add(self.request.user)
        return super().form_valid(form)


class SiaeEditInfoContactView(LoginRequiredMixin, SiaeOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditInfoContactForm
    template_name = "dashboard/siae_edit_info_contact.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_info_contact", args=[self.kwargs.get("pk")])


class SiaeEditOfferView(LoginRequiredMixin, SiaeOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditOfferForm
    template_name = "dashboard/siae_edit_offer.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_offer", args=[self.kwargs.get("pk")])


class SiaeEditPrestaView(LoginRequiredMixin, SiaeOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditPrestaForm
    template_name = "dashboard/siae_edit_presta.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["offer_formset"] = SiaeOfferFormSet(self.request.POST, instance=self.object)
            data["client_reference_formset"] = SiaeClientReferenceFormSet(self.request.POST, instance=self.object)
        else:
            data["offer_formset"] = SiaeOfferFormSet(instance=self.object)
            data["client_reference_formset"] = SiaeClientReferenceFormSet(instance=self.object)
        return data

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        offer_formset = SiaeOfferFormSet(self.request.POST, instance=self.object)
        client_reference_formset = SiaeClientReferenceFormSet(self.request.POST, instance=self.object)
        if form.is_valid() and offer_formset.is_valid() and client_reference_formset.is_valid():
            return self.form_valid(form, offer_formset, client_reference_formset)
        else:
            return self.form_invalid(form, offer_formset, client_reference_formset)

    def form_valid(self, form, offer_formset, client_reference_formset):
        self.object = form.save()
        offer_formset.instance = self.object
        offer_formset.save()
        client_reference_formset.instance = self.object
        client_reference_formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, offer_formset, client_reference_formset):
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_presta", args=[self.kwargs.get("pk")])


class SiaeEditOtherView(LoginRequiredMixin, SiaeOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditOtherForm
    template_name = "dashboard/siae_edit_other.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["label_formset"] = SiaeLabelFormSet(self.request.POST, instance=self.object)
        else:
            data["label_formset"] = SiaeLabelFormSet(instance=self.object)
        return data

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        label_formset = SiaeLabelFormSet(self.request.POST, instance=self.object)
        if form.is_valid() and label_formset.is_valid():
            return self.form_valid(form, label_formset)
        else:
            return self.form_invalid(form, label_formset)

    def form_valid(self, form, label_formset):
        self.object = form.save()
        label_formset.instance = self.object
        label_formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, label_formset):
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_other", args=[self.kwargs.get("pk")])
