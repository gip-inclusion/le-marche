from django.urls import path
from django.views.generic import RedirectView

from lemarche.www.tenders.views import (
    TenderCreateMultiStepView,
    TenderDetailContactClickStat,
    TenderDetailSurveyTransactionedView,
    TenderDetailView,
    TenderListView,
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
    path(
        "<str:slug>/structures-interessees",
        RedirectView.as_view(pattern_name="tenders:detail-siae-list", permanent=True),
        name="detail-siae-list-old",
    ),  # TODO: delete in 2024
    path("<str:slug>/prestataires/statut/<status>", TenderSiaeListView.as_view(), name="detail-siae-list"),
    path("<str:slug>/prestataires", TenderSiaeListView.as_view(), name="detail-siae-list"),
    path("<str:slug>/contact-click-stat", TenderDetailContactClickStat.as_view(), name="detail-contact-click-stat"),
    path(
        "<str:slug>/sondage-transaction",
        TenderDetailSurveyTransactionedView.as_view(),
        name="detail-survey-transactioned",
    ),
]
