from django.urls import path

from lemarche.www.jobs.views import SectorAppellationsView


app_name = "jobs"

urlpatterns = [
    path("secteur/appellations/", SectorAppellationsView.as_view(), name="sector-appellations"),
]
