from django.urls import path

from lemarche.www.jobs.views import SectorAppellationsFormView, SectorAppellationsView


app_name = "jobs"

urlpatterns = [
    path("secteur/", SectorAppellationsFormView.as_view(), name="sector-appellations-form"),
    path("secteur/metiers/", SectorAppellationsView.as_view(), name="sector-appellations"),
]
