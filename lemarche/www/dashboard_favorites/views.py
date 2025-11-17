from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Exists, OuterRef
from django.db.models.query import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import CreateView

from lemarche.favorites.models import FavoriteItem, FavoriteList
from lemarche.networks.models import Network
from lemarche.siaes.models import Siae
from lemarche.utils import settings_context_processors
from lemarche.utils.mixins import FavoriteListOwnerRequiredMixin
from lemarche.www.dashboard_favorites.forms import FavoriteListEditForm


class DashboardFavoriteListView(LoginRequiredMixin, ListView):
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
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")},
            ],
            "current": settings.FAVORITE_LIST_TITLE,
        }
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
        return format_html("Votre liste d'achat <strong>{}</strong> a été créée avec succès.", cleaned_data["name"])


class DashboardFavoriteListDetailView(FavoriteListOwnerRequiredMixin, DetailView):
    template_name = "favorites/dashboard_favorite_list_detail.html"
    queryset = FavoriteList.objects.prefetch_related(
        Prefetch(
            "siaes",
            Siae.objects.annotate(
                is_in_the_hosmoz_network=Exists(Network.objects.filter(slug="hosmoz", siaes__pk=OuterRef("pk")))
            ),
        ),
        "siaes__activities__sector__group",
    ).all()
    context_object_name = "favorite_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")},
                {"title": settings.FAVORITE_LIST_TITLE, "url": reverse_lazy("dashboard_favorites:list")},
            ],
            "current": self.object.name,
        }
        return context


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
        return format_html("Votre liste d'achat <strong>{}</strong> a été supprimée avec succès.", self.object.name)


class DashboardFavoriteItemDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "favorites/_favorite_item_remove_modal.html"
    model = FavoriteItem

    def get_object(self):
        """
        - there should theoretically be only 1 Siae per user's lists (an Siae cannot belong to other list)
        - in the future it could be possible to add an Siae to multiple user lists
        """
        siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        return get_object_or_404(FavoriteItem, favorite_list__user=self.request.user, siae=siae)

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        else:
            return reverse_lazy(
                "dashboard_favorites:list_detail",
                kwargs={
                    "slug": self.object.favorite_list.slug,
                },
            )

    def get_success_message(self, cleaned_data):
        return format_html(
            "<strong>{}</strong> a été supprimée de votre liste d'achat avec succès.",
            self.object.siae.name_display,
        )
