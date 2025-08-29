from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import DetailView, FormView, UpdateView
from django_filters.views import FilterView

from content_manager.models import ContentPage, Tag
from lemarche.cms.models import ArticleList
from lemarche.purchases.models import Purchase
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.www.dashboard.filters import PurchaseFilterSet
from lemarche.www.dashboard.forms import DisabledEmailEditForm, ProfileEditForm


SLUG_RESSOURCES_CAT_SIAES = "solutions"
SLUG_RESSOURCES_CAT_BUYERS = "acheteurs"


class DashboardHomeView(LoginRequiredMixin, DetailView):
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


class InclusivePurchaseStatsDashboardView(LoginRequiredMixin, FilterView):
    filterset_class = PurchaseFilterSet
    template_name = "dashboard/inclusive_purchase_stats.html"

    def get_queryset(self):
        return Purchase.objects.get_purchase_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.kind != User.KIND_BUYER and user.company is None:
            return context

        # get purchase stats for the user
        purchases_stats = self.filterset.qs.with_stats()
        total_purchases = purchases_stats["total_amount_annotated"]
        if total_purchases > 0:
            chart_data_inclusive = {
                "labels": ["Achats inclusifs", "Achats non inclusifs"],
                "dataset": [
                    purchases_stats["total_inclusive_amount_annotated"],
                    purchases_stats["total_amount_annotated"] - (purchases_stats["total_inclusive_amount_annotated"]),
                ],
            }
            chart_data_insertion_handicap = {
                "labels": ["Structures d'insertion (IAE)", "Structures du Handicap (STPA)"],
                "dataset": [
                    purchases_stats["total_insertion_amount_annotated"],
                    purchases_stats["total_handicap_amount_annotated"],
                ],
            }
            chart_data_siae_type = {
                "labels": [
                    kind
                    for kind in KIND_INSERTION_LIST + KIND_HANDICAP_LIST
                    if purchases_stats[f"total_purchases_by_kind_{kind}"] > 0
                ],
                "dataset": [
                    purchases_stats[f"total_purchases_by_kind_{kind}"]
                    for kind in KIND_INSERTION_LIST + KIND_HANDICAP_LIST
                    if purchases_stats[f"total_purchases_by_kind_{kind}"] > 0
                ],
            }
            purchase_categories = list(self.filterset.qs.values_list("purchase_category", flat=True).distinct())
            chart_data_purchases_by_category = {
                "labels": purchase_categories,
                "dataset": [
                    purchases_stats[f"total_purchases_by_category_{purchase_category}"]
                    for purchase_category in purchase_categories
                    if purchases_stats[f"total_purchases_by_category_{purchase_category}"] > 0
                ],
            }

            buying_entities = list(self.filterset.qs.values_list("buying_entity", flat=True).distinct())
            chart_data_purchases_by_buying_entity = {
                "labels": buying_entities,
                "dataset": [
                    purchases_stats[f"total_purchases_by_buying_entity_{slugify(buying_entity)}"]
                    for buying_entity in buying_entities
                    if purchases_stats[f"total_purchases_by_buying_entity_{slugify(buying_entity)}"] > 0
                ],
            }

            context.update(
                {
                    "total_purchases": purchases_stats["total_amount_annotated"],
                    "total_suppliers": purchases_stats["total_suppliers_annotated"],
                    "total_inclusive_suppliers": purchases_stats["total_inclusive_suppliers_annotated"],
                    "total_inclusive_purchases": purchases_stats["total_inclusive_amount_annotated"],
                    "total_insertion_purchases": purchases_stats["total_insertion_amount_annotated"],
                    "total_handicap_purchases": purchases_stats["total_handicap_amount_annotated"],
                    "total_inclusive_purchases_percentage": round(
                        purchases_stats["total_inclusive_amount_annotated"] * 100 / total_purchases,
                        2,
                    ),
                    "total_insertion_purchases_percentage": round(
                        purchases_stats["total_insertion_amount_annotated"] * 100 / total_purchases,
                        2,
                    ),
                    "total_handicap_purchases_percentage": round(
                        purchases_stats["total_handicap_amount_annotated"] * 100 / total_purchases,
                        2,
                    ),
                    "chart_data_inclusive": chart_data_inclusive,
                    "chart_data_insertion_handicap": chart_data_insertion_handicap,
                    "chart_data_siae_type": chart_data_siae_type,
                    "chart_data_purchases_by_category": chart_data_purchases_by_category,
                    "chart_data_purchases_by_buying_entity": chart_data_purchases_by_buying_entity,
                }
            )
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
