from django.urls import path

from lemarche.www.dashboard_favorites.views import (
    ProfileFavoriteItemDeleteView,
    ProfileFavoriteListCreateView,
    ProfileFavoriteListDeleteView,
    ProfileFavoriteListDetailView,
    ProfileFavoriteListEditView,
    ProfileFavoriteListView,
)


app_name = "dashboard_favorites"

urlpatterns = [
    path("", ProfileFavoriteListView.as_view(), name="list"),
    path("creer/", ProfileFavoriteListCreateView.as_view(), name="list_create"),
    path("<str:slug>/", ProfileFavoriteListDetailView.as_view(), name="list_detail"),
    path(
        "<slug:slug>/prestataires/<slug:siae_slug>/",
        ProfileFavoriteItemDeleteView.as_view(),
        name="item_delete",
    ),
    path("<str:slug>/modifier/", ProfileFavoriteListEditView.as_view(), name="list_edit"),
    path(
        "<str:slug>/supprimer/",
        ProfileFavoriteListDeleteView.as_view(),
        name="list_delete",
    ),
]
