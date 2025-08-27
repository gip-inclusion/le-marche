from django.urls import path
from django.views.generic import TemplateView

from lemarche.www.pages.views import (
    CompanyReferenceCalculatorView,
    ContactView,
    ImpactCalculatorView,
    SiaeGroupListView,
    SitemapView,
    SocialImpactBuyersCalculatorView,
    StatsView,
    trigger_error,
)


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "pages"

urlpatterns = [
    path("contact/", ContactView.as_view(), name="contact"),
    # Calculator endpoints
    path("calibrer-achat-socialement-responsable/", ImpactCalculatorView.as_view(), name="impact_calculator"),
    path(
        "calculer-impact-social-achat-inclusif/",
        SocialImpactBuyersCalculatorView.as_view(),
        name="buyer_social_impact_calculator",
    ),
    path("acheteurs-reference-client/", CompanyReferenceCalculatorView.as_view(), name="company_reference_calculator"),
    # Other dynamic pages
    path("groupements/", SiaeGroupListView.as_view(), name="groupements"),
    path("stats/", StatsView.as_view(), name="stats"),
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
    # Sentry endpoint for frontend errors
    path("sentry-debug/", trigger_error, name="sentry_debug"),
    path("plan-du-site/", SitemapView.as_view(), name="plan-du-site"),
    # Error pages
    path("403/", TemplateView.as_view(template_name="403.html"), name="403"),
    path("404/", TemplateView.as_view(template_name="404.html"), name="404"),
    path("429/", TemplateView.as_view(template_name="429.html"), name="429"),
    path("500/", TemplateView.as_view(template_name="500.html"), name="500"),
]
