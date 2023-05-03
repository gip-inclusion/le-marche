from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import CreateView

from lemarche.favorites.models import FavoriteItem, FavoriteList
from lemarche.siaes.models import Siae
from lemarche.utils.mixins import FavoriteListOwnerRequiredMixin
from lemarche.www.dashboard_favorites.forms import FavoriteListEditForm


class DashboardFavoriteListView(LoginRequiredMixin, ListView):
    # form_class = FavoriteListEditForm
    template_name = "favorites/dashboard_favorite_list.html"
    queryset = FavoriteList.objects.all()
    context_object_name = "favorite_lists"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.by_user(user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = FavoriteListEditForm()
        return context


class DashboardFavoriteListCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = FavoriteListEditForm
    # success_message = "Votre liste d'achat a été crée avec succès."
    success_url = reverse_lazy("dashboard_favorites:list")

    def form_valid(self, form):
        """Add the User to the FavoriteList."""
        favorite_list = form.save(commit=False)
        favorite_list.user = self.request.user
        favorite_list.save()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data),
        )
        return HttpResponseRedirect(self.success_url)

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre liste d'achat <strong>{cleaned_data['name']}</strong> a été crée avec succès.")


class DashboardFavoriteListDetailView(FavoriteListOwnerRequiredMixin, DetailView):
    template_name = "favorites/dashboard_favorite_list_detail.html"
    queryset = FavoriteList.objects.prefetch_related("siaes").all()
    context_object_name = "favorite_list"


class DashboardFavoriteListEditView(FavoriteListOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = FavoriteListEditForm
    template_name = "favorites/_favorite_list_edit_modal.html"
    success_message = "Votre liste d'achat a été modifiée avec succès."
    # success_url = reverse_lazy("dashboard_favorites:list_detail")

    def get_object(self):
        return get_object_or_404(FavoriteList, slug=self.kwargs.get("slug"))

    def get_success_url(self):
        return reverse_lazy("dashboard_favorites:list_detail", args=[self.kwargs.get("slug")])


class DashboardFavoriteListDeleteView(FavoriteListOwnerRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "favorites/_favorite_list_delete_modal.html"
    model = FavoriteList
    # success_message = "Votre liste d'achat a été supprimée avec succès."
    success_url = reverse_lazy("dashboard_favorites:list")

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre liste d'achat <strong>{self.object.name}</strong> a été supprimée avec succès.")


class DashboardFavoriteItemDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    # FavoriteListOwnerRequiredMixin  # doesn't work because we don't have the FavoriteList slug
    template_name = "favorites/_favorite_item_remove_modal.html"
    model = FavoriteItem
    # success_message = "La structure a été supprimée de votre liste d'achat avec succès."
    success_url = reverse_lazy("dashboard_favorites:list_detail")

    def get_object(self):
        """
        - there should theoretically be only 1 Siae per user's lists (an Siae cannot belong to other list)
        - in the future it could be possible to add an Siae to multiple user lists
        """
        # try:
        #     favorite_list = FavoriteList.objects.get(slug=self.kwargs.get("slug"))
        #     siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        #     return get_object_or_404(FavoriteItem, favorite_list=favorite_list, siae=siae)
        # except:  # noqa
        #     raise Http404
        siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        return get_object_or_404(FavoriteItem, favorite_list__user=self.request.user, siae=siae)

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        return super().get_success_url()

    def get_success_message(self, cleaned_data):
        return mark_safe(
            f"<strong>{self.object.siae.name_display}</strong> a été supprimée de votre liste d'achat avec succès."
        )
