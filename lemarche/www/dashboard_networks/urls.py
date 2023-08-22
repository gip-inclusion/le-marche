from django.urls import path

from lemarche.www.dashboard_networks.views import (
    DashboardNetworkDetailView,
    DashboardNetworkSiaeListView,
    DashboardNetworkSiaeTenderListView,
    DashboardNetworkTenderDetailView,
    DashboardNetworkTenderListView,
    DashboardNetworkTenderSiaeListView,
)


app_name = "dashboard_networks"

urlpatterns = [
    path("<str:slug>/", DashboardNetworkDetailView.as_view(), name="detail"),
    path("<str:slug>/prestataires/", DashboardNetworkSiaeListView.as_view(), name="siae_list"),
    path(
        "<str:slug>/prestataires/<slug:siae_slug>/besoins/<status>",
        DashboardNetworkSiaeTenderListView.as_view(),
        name="siae_tender_list",
    ),
    path(
        "<str:slug>/prestataires/<slug:siae_slug>/besoins/",
        DashboardNetworkSiaeTenderListView.as_view(),
        name="siae_tender_list",
    ),
    path("<str:slug>/besoins/", DashboardNetworkTenderListView.as_view(), name="tender_list"),
    path(
        "<str:slug>/besoins/<slug:tender_slug>/prestataires/<status>",
        DashboardNetworkTenderSiaeListView.as_view(),
        name="tender_siae_list",
    ),
    path(
        "<str:slug>/besoins/<slug:tender_slug>/prestataires/",
        DashboardNetworkTenderSiaeListView.as_view(),
        name="tender_siae_list",
    ),
    path(
        "<str:slug>/besoins/<slug:tender_slug>/",
        DashboardNetworkTenderDetailView.as_view(),
        name="tender_detail",
    ),
]
