from django.urls import path
from django.views.generic import TemplateView

from lemarche.www.pages.views import (
    CompanyReferenceCalculatorView,
    ContactView,
    HomeView,
    ImpactCalculatorView,
    PageView,
    SiaeGroupListView,
    SocialImpactBuyersCalculatorView,
    StatsView,
    TrackView,
    trigger_error,
)


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
        name="decouvrir_inclusion",
    ),
    path(
        "partenaires/",
        TemplateView.as_view(template_name="pages/partenaires.html"),
        name="partenaires",
    ),
    path(
        "valoriser-achats/",
        TemplateView.as_view(template_name="pages/valoriser-achats.html"),
        name="valoriser_achats",
    ),
    path(
        "accessibilite/",
        TemplateView.as_view(template_name="pages/accessibilite.html"),
        name="accessibilite",
    ),
    path("groupements/", SiaeGroupListView.as_view(), name="groupements"),
    path("stats/", StatsView.as_view(), name="stats"),
    # Sentry endpoint for frontend errors
    path("sentry-debug/", trigger_error, name="sentry_debug"),
    # Tracking endpoint for the frontend
    path("track/", TrackView.as_view(), name="track_frontend"),
    # Calculator endpoints
    path("calibrer-achat-socialement-responsable/", ImpactCalculatorView.as_view(), name="impact_calculator"),
    path(
        "calculer-impact-social-achat-inclusif/",
        SocialImpactBuyersCalculatorView.as_view(),
        name="buyer_social_impact_calculator",
    ),
    path("acheteurs-reference-client/", CompanyReferenceCalculatorView.as_view(), name="company_reference_calculator"),
    # Flatpages (created in the admin)
    # path("", include("django.contrib.flatpages.urls")),
    path("<path:url>", PageView.as_view(), name="flatpage"),
    # Error pages
    path("403/", TemplateView.as_view(template_name="403.html"), name="403"),
    path("404/", TemplateView.as_view(template_name="404.html"), name="404"),
    path("500/", TemplateView.as_view(template_name="500.html"), name="500"),
]
