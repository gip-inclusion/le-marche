from django.urls import path

from lemarche.www.dashboard.views import (
    DashboardHomeView,
    DisabledEmailEditView,
    InclusivePurchaseStatsDashboardView,
    InviteColleaguesView,
    ProfileEditView,
)


app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("modifier/", ProfileEditView.as_view(), name="profile_edit"),
    path("notifications/", DisabledEmailEditView.as_view(), name="notifications_edit"),
    path("part-achat-inclusif/", InclusivePurchaseStatsDashboardView.as_view(), name="inclusive_purchase_stats"),
    path("inviter-collegues/", InviteColleaguesView.as_view(), name="invite_colleagues"),
    # FavoriteList
    # see dashboard_favorites/urls.py
    # Network
    # see dashboard_networks/urls.py
    # Adopt Siae, Edit Siae & Siae Users
    # see dashboard_siaes/urls.py
]
