from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, UpdateView

from content_manager.models import ContentPage, Tag
from lemarche.cms.models import ArticleList
from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.www.dashboard.forms import DisabledEmailEditForm, ProfileEditForm


SLUG_RESSOURCES_CAT_SIAES = "solutions"
SLUG_RESSOURCES_CAT_BUYERS = "acheteurs"


class DashboardHomeView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    context_object_name = "user"

    def test_func(self):
        return self.request.user.is_onboarded

    def get_object(self):
        return self.request.user

    def get_template_names(self):
        if self.request.user.kind == User.KIND_SIAE:
            return ["dashboard/home_siae.html"]
        return ["dashboard/home_buyer.html"]

    def get(self, request, *args, **kwargs):
        """
        Update 'dashboard_last_seen_date'
        """
        user = self.request.user
        if user.is_authenticated:
            User.objects.filter(id=user.id).update(dashboard_last_seen_date=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # filter ressources by user kind
        category_slug = None
        if user.kind == User.KIND_SIAE:
            category_slug = SLUG_RESSOURCES_CAT_SIAES
        elif user.kind == User.KIND_BUYER:
            category_slug = SLUG_RESSOURCES_CAT_BUYERS

        # Get ContentPage under the ArticleList that has the slug "ressources"
        try:
            ressource_page = ArticleList.objects.get(slug="ressources")
            ressource_list = (
                ContentPage.objects.descendant_of(ressource_page)
                .live()
                .prefetch_related("tags")
                .order_by("-last_published_at")
            )
        except ArticleList.DoesNotExist:
            ressource_list = ContentPage.objects.none()

        if category_slug:
            try:
                tag = Tag.objects.get(slug=category_slug)
                ressource_list = ressource_list.filter(tags__in=[tag])
            except Exception:
                pass

        # set context ressources
        context["last_3_ressources"] = ressource_list[:3]

        # for specific users
        if user.kind == User.KIND_SIAE:
            siaes = user.siaes.all()
            if siaes:
                context["last_3_tenders"] = Tender.objects.filter_with_siaes(siaes).order_by_last_published()[:3]
        else:
            context["last_3_tenders"] = Tender.objects.filter(author=user).order_by_last_published()[:3]
            context["user_buyer_count"] = User.objects.filter(kind=User.KIND_BUYER).count()
            context["siae_count"] = Siae.objects.is_live().count()
            context["tender_count"] = Tender.objects.sent().count() + 30  # historic number (before form)
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = "dashboard/profile_edit.html"
    success_message = "Votre profil a été mis à jour."
    success_url = reverse_lazy("dashboard:home")

    def get_object(self):
        return self.request.user


class DisabledEmailEditView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    form_class = DisabledEmailEditForm
    template_name = "dashboard/disabled_email_edit.html"
    success_url = reverse_lazy("dashboard:notifications_edit")
    success_message = "Vos préférences de notifications ont été mises à jour."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
