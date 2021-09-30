from django.urls import path

from lemarche.www.dashboard.views import DashboardHomeView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
]
