from django.urls import path
from django.views.generic import RedirectView

from lemarche.www.tenders.views import (
    TenderCreateMultiStepView,
    TenderDetailContactClickStatView,
    TenderDetailNotInterestedClickView,
    TenderDetailSiaeSurveyTransactionedView,
    TenderDetailSurveyTransactionedView,
    TenderDetailView,
    TenderListView,
    TenderReminderView,
    TenderSiaeHideView,
    TenderSiaeInterestedDownloadView,
    TenderSiaeListView,
)


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "tenders"

urlpatterns = [
    # why redirect? avoid conflict with tenders:detail
    path("ajouter", RedirectView.as_view(pattern_name="tenders:create", permanent=True), name="create_without_slash"),
    path("ajouter/", TenderCreateMultiStepView.as_view(), name="create"),
    path("modifier/<str:slug>", TenderCreateMultiStepView.as_view(), name="update"),
    path("<str:slug>", TenderDetailView.as_view(), name="detail"),
    path("statut/<status>", TenderListView.as_view(), name="list"),
    path("", TenderListView.as_view(), name="list"),
    path("<str:slug>/prestataires/statut/<status>", TenderSiaeListView.as_view(), name="detail-siae-list"),
    path("<str:slug>/prestataires", TenderSiaeListView.as_view(), name="detail-siae-list"),
    path(
        "<str:slug>/prestataires/telechargement", TenderSiaeInterestedDownloadView.as_view(), name="download-siae-list"
    ),
    path("<str:slug>/prestataires/statut/<status>/reminder", TenderReminderView.as_view(), name="send-reminder"),
    path(
        "<slug:slug>/contact-click-stat", TenderDetailContactClickStatView.as_view(), name="detail-contact-click-stat"
    ),
    path(
        "<str:slug>/not-interested-click",
        TenderDetailNotInterestedClickView.as_view(),
        name="detail-not-interested-click",
    ),
    path(
        "<str:slug>/cacher-depot-de-besoin",
        TenderSiaeHideView.as_view(),
        name="hide-tender-siae",
    ),
    path(
        "<str:slug>/sondage-transaction",
        TenderDetailSurveyTransactionedView.as_view(),
        name="detail-survey-transactioned",
    ),
    path(
        "<str:slug>/prestataires/<str:siae_slug>/sondage-transaction",
        TenderDetailSiaeSurveyTransactionedView.as_view(),
        name="detail-siae-survey-transactioned",
    ),
]
