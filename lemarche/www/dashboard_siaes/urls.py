from django.urls import include, path
from django.views.generic.base import RedirectView

from lemarche.www.dashboard_siaes.views import (
    SiaeEditContactView,
    SiaeEditInfoView,
    SiaeEditLinksView,
    SiaeEditOfferView,
    SiaeEditSearchView,
    SiaeSearchAdoptConfirmView,
    SiaeSearchBySiretView,
    SiaeUserDeleteView,
    SiaeUserRequestCancelView,
    SiaeUserRequestConfirmView,
    SiaeUsersView,
)


app_name = "dashboard_siaes"

urlpatterns = [
    path("rechercher/", SiaeSearchBySiretView.as_view(), name="siae_search_by_siret"),
    path("<str:slug>/adopter/", SiaeSearchAdoptConfirmView.as_view(), name="siae_search_adopt_confirm"),
    # Edit Siae
    path(
        "<str:slug>/modifier/",
        include(
            [
                path(
                    "",
                    RedirectView.as_view(pattern_name="dashboard:siae_edit_contact", permanent=False),
                    name="siae_edit",
                ),
                path("contact/", SiaeEditContactView.as_view(), name="siae_edit_contact"),
                path("recherche/", SiaeEditSearchView.as_view(), name="siae_edit_search"),
                path("info/", SiaeEditInfoView.as_view(), name="siae_edit_info"),
                path("offre/", SiaeEditOfferView.as_view(), name="siae_edit_offer"),
                path("liens/", SiaeEditLinksView.as_view(), name="siae_edit_links"),
            ]
        ),
    ),
    # Edit Siae (old urls: redirect)
    path(
        "<str:slug>/modifier/info-contact/",
        RedirectView.as_view(pattern_name="dashboard:siae_edit_search", permanent=True),
        name="siae_edit_info_contact_old",
    ),
    path(
        "<str:slug>/modifier/prestations/",
        RedirectView.as_view(pattern_name="dashboard:siae_edit_search", permanent=True),
        name="siae_edit_info_presta_old",
    ),
    path(
        "<str:slug>/modifier/autre/",
        RedirectView.as_view(pattern_name="dashboard:siae_edit_search", permanent=True),
        name="siae_edit_other_old",
    ),
    # Siae Users (& Requests)
    path(
        "<str:slug>/collaborateurs/",
        SiaeUsersView.as_view(),
        name="siae_users",
    ),
    path(
        "<str:slug>/collaborateurs/<str:siaeuserrequest_id>/accepter",
        SiaeUserRequestConfirmView.as_view(),
        name="siae_user_request_confirm",
    ),
    path(
        "<str:slug>/collaborateurs/<str:siaeuserrequest_id>/refuser",
        SiaeUserRequestCancelView.as_view(),
        name="siae_user_request_cancel",
    ),
    path(
        "<str:slug>/collaborateurs/<str:siaeuser_id>/supprimer",
        SiaeUserDeleteView.as_view(),
        name="siae_user_delete",
    ),
    # Redirects
    path(
        "<str:slug>/",
        RedirectView.as_view(pattern_name="dashboard:siae_users", permanent=False),
        name="siae",
    ),
    path(
        "",
        RedirectView.as_view(pattern_name="dashboard:siae_search_by_siret", permanent=False),
        name="siae_search",
    ),
]
