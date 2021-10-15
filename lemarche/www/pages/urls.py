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
        "filiere/restauration/",
        TemplateView.as_view(template_name="pages/filiere_restauration.html"),
        name="filiere_restauration",
    ),
    path(
        "filiere/recyclage/",
        TemplateView.as_view(template_name="pages/filiere_recyclage.html"),
        name="filiere_recyclage",
    ),
    path(
        "decouvrir-inclusion/",
        TemplateView.as_view(template_name="pages/decouvrir-inclusion.html"),
        name="decouvrir-inclusion",
    ),
    # Flatpages (created in the admin)
    # path("", include("django.contrib.flatpages.urls")),
    path("<path:url>", PageView.as_view(), name="flatpage"),
    # TODO: Add sentry
    # path("sentry-debug/", views.trigger_error, name="sentry_debug"),
]
