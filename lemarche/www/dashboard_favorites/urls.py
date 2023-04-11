from django.urls import path

from lemarche.www.dashboard_favorites.views import (
    DashboardFavoriteItemDeleteView,
    DashboardFavoriteListCreateView,
    DashboardFavoriteListDeleteView,
    DashboardFavoriteListDetailView,
    DashboardFavoriteListEditView,
    DashboardFavoriteListView,
)


app_name = "dashboard_favorites"

urlpatterns = [
    path("", DashboardFavoriteListView.as_view(), name="list"),
    path("creer/", DashboardFavoriteListCreateView.as_view(), name="list_create"),
    path("<str:slug>/", DashboardFavoriteListDetailView.as_view(), name="list_detail"),
    path(
        "<slug:slug>/prestataires/<slug:siae_slug>/",
        DashboardFavoriteItemDeleteView.as_view(),
        name="item_delete",
    ),
    path("<str:slug>/modifier/", DashboardFavoriteListEditView.as_view(), name="list_edit"),
    path(
        "<str:slug>/supprimer/",
        DashboardFavoriteListDeleteView.as_view(),
        name="list_delete",
    ),
]
