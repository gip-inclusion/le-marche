from django.urls import path

from lemarche.www.dashboard.views import (
    DashboardHomeView,
    DisabledEmailEditView,
    InclusivePurchaseStatsDashboardView,
    ProfileEditView,
)


app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("modifier/", ProfileEditView.as_view(), name="profile_edit"),
    path("notifications/", DisabledEmailEditView.as_view(), name="notifications_edit"),
    path("part-achat-inclusif/", InclusivePurchaseStatsDashboardView.as_view(), name="inclusive_purchase_stats"),
    # FavoriteList
    # see dashboard_favorites/urls.py
    # Network
    # see dashboard_networks/urls.py
    # Adopt Siae, Edit Siae & Siae Users
    # see dashboard_siaes/urls.py
]
