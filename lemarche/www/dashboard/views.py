from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.siaes.models import Siae
from lemarche.www.dashboard.forms import ProfileEditForm, SiaeAdoptConfirmForm, SiaeSearchBySiretForm


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


class SiaeSearchBySiretView(LoginRequiredMixin, FormMixin, ListView):
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
        - initialize the form with the query parameters
        """
        context = super().get_context_data(**kwargs)
        if "siret" in self.request.GET:
            context["form"] = SiaeSearchBySiretForm(data=self.request.GET)
        return context


class SiaeAdoptConfirmView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeAdoptConfirmForm
    template_name = "dashboard/siae_adopt_confirm.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Votre structure a été rajoutée dans votre espace."
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        """Add the Siae to the User."""
        self.object.users.add(self.request.user)
        return super().form_valid(form)
