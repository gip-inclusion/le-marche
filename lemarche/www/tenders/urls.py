from django.urls import path

from lemarche.www.tenders.views import (
    TenderCreateMultiStepView,
    TenderDetailContactClickStat,
    TenderDetailView,
    TenderListView,
    TenderSiaeInterestedListView,
)


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "tenders"

urlpatterns = [
    path("ajouter/", TenderCreateMultiStepView.as_view(), name="create"),
    path("ajouter/<str:slug>", TenderCreateMultiStepView.as_view(), name="create"),
    path("<str:slug>", TenderDetailView.as_view(), name="detail"),
    path("status/<status>", TenderListView.as_view(), name="list"),
    path("", TenderListView.as_view(), name="list"),
    path("<str:slug>/structures-interessees", TenderSiaeInterestedListView.as_view(), name="detail-siae-interested"),
    path("<str:slug>/contact-click-stat", TenderDetailContactClickStat.as_view(), name="detail-contact-click-stat"),
]
