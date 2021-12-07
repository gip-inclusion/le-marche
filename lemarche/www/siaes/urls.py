from django.urls import path

from lemarche.www.siaes.views import (
    SiaeDetailView,
    SiaeFavoriteView,
    SiaeSearchResultsDownloadView,
    SiaeSearchResultsView,
)


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "siae"

urlpatterns = [
    path("", SiaeSearchResultsView.as_view(), name="search_results"),
    path("download/", SiaeSearchResultsDownloadView.as_view(), name="search_results_download"),
    path("<str:slug>/", SiaeDetailView.as_view(), name="detail"),
    path("<str:slug>/favoris/", SiaeFavoriteView.as_view(), name="favorite_lists"),
]
