from django.urls import path

from lemarche.www.siae.views import SiaeSearchResultsView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "siae"

urlpatterns = [
    path("", SiaeSearchResultsView.as_view(), name="search_results"),
]
