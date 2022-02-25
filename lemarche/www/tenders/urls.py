from django.urls import path

from lemarche.www.tenders.views import AddTenderView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "tenders"

urlpatterns = [
    path("ajouter", AddTenderView.as_view(), name="add"),
]
