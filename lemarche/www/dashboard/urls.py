from django.urls import path

from lemarche.www.dashboard.views import (
    DashboardHomeView,
    ProfileEditView,
    SiaeAdoptConfirmView,
    SiaeSearchBySiretView,
)


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("profile-edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("siae/search/", SiaeSearchBySiretView.as_view(), name="siae_search_by_siret"),
    path("siae/<int:pk>/adopt-confirm/", SiaeAdoptConfirmView.as_view(), name="siae_adopt_confirm"),
]
