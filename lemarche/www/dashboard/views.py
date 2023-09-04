from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, UpdateView

from lemarche.cms.models import ArticlePage
from lemarche.cms.snippets import ArticleCategory
from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.www.dashboard.forms import ProfileEditForm


SLUG_RESSOURCES_CAT_SIAES = "solutions"
SLUG_RESSOURCES_CAT_BUYERS = "acheteurs"


class DashboardHomeView(LoginRequiredMixin, DetailView):
    # template_name = "dashboard/home.html"
    context_object_name = "user"

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
        article_list = ArticlePage.objects.live().public().order_by("-last_published_at")

        if category_slug:
            try:
                # Look for the blog category by its slug.
                category = ArticleCategory.objects.get(slug=category_slug)
                article_list = article_list.filter(categories__in=[category])
            except Exception:
                category_slug = None

        # set context ressources
        context["current_slug_cat"] = category_slug
        context["last_3_ressources"] = article_list[:3]

        # for specific users
        if user.kind == User.KIND_SIAE:
            siaes = user.siaes.all()
            if siaes:
                context["last_3_tenders"] = Tender.objects.filter_with_siaes(siaes).order_by_deadline_date()[:3]
        else:
            context["last_3_tenders"] = Tender.objects.filter(author=user).order_by_deadline_date()[:3]
            context["user_buyer_count"] = User.objects.filter(kind=User.KIND_BUYER).count()
            context["siae_count"] = Siae.objects.is_live().count()
            context["tender_count"] = Tender.objects.validated().count() + 30  # historic number (before form)
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = "dashboard/profile_edit.html"
    success_message = "Votre profil a été mis à jour."
    success_url = reverse_lazy("dashboard:home")

    def get_object(self):
        return self.request.user
