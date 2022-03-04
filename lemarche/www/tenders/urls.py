from django.urls import path

from lemarche.www.tenders.views import TenderAddView, TenderDetail, TenderListView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "tenders"

urlpatterns = [
    path("ajouter", TenderAddView.as_view(), name="add"),
    path("liste", TenderListView.as_view(), name="list"),
    path("<str:slug>", TenderDetail.as_view(), name="detail"),
]
