from django.urls import path
from django.views.generic import TemplateView

from lemarche.www.pages.views import ContactView, HomeView, PageView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "pages"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    # Static pages
    path(
        "cest-quoi-linclusion/",
        TemplateView.as_view(template_name="pages/cest-quoi-linclusion.html"),
        name="cest-quoi-linclusion",
    ),
    # Flatpages (created in the admin)
    # path("", include("django.contrib.flatpages.urls")),
    path("<path:url>", PageView.as_view(), name="flatpage"),
    # TODO: Add sentry
    # path("sentry-debug/", views.trigger_error, name="sentry_debug"),
]
