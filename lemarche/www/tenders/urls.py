from django.urls import path

from lemarche.www.tenders.views import TenderCreateView, TenderDetail, TenderDetailContactClickStat, TenderListView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "tenders"

urlpatterns = [
    path("ajouter", TenderCreateView.as_view(), name="create"),
    path("", TenderListView.as_view(), name="list"),
    path("<str:slug>", TenderDetail.as_view(), name="detail"),
    path("<str:slug>/contact-click-stat", TenderDetailContactClickStat.as_view(), name="detail-contact-click-stat"),
]
