from django.urls import include, path
from django.views.generic.base import RedirectView

from lemarche.www.dashboard.views import (
    DashboardHomeView,
    ProfileEditView,
    SiaeEditInfoContactView,
    SiaeEditOfferView,
    SiaeEditOtherView,
    SiaeEditPrestaView,
    SiaeSearchAdoptConfirmView,
    SiaeSearchBySiretView,
)


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("profile-edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("siae/search/", SiaeSearchBySiretView.as_view(), name="siae_search_by_siret"),
    path("siae/<int:pk>/adopt-confirm/", SiaeSearchAdoptConfirmView.as_view(), name="siae_search_adopt_confirm"),
    path(
        "siae/<int:pk>/edit/",
        include(
            [
                path(
                    "",
                    RedirectView.as_view(pattern_name="dashboard:siae_edit_info_contact", permanent=False),
                    name="siae_edit",
                ),
                path("contact/", SiaeEditInfoContactView.as_view(), name="siae_edit_info_contact"),
                path("offer/", SiaeEditOfferView.as_view(), name="siae_edit_offer"),
                path("presta/", SiaeEditPrestaView.as_view(), name="siae_edit_presta"),
                path("other/", SiaeEditOtherView.as_view(), name="siae_edit_other"),
            ]
        ),
    ),
]
