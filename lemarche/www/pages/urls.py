from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from lemarche.www.pages.views import ContactView, HomeView, PageView, StatsView, trigger_error


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
    path("stats/", StatsView.as_view(), name="stats"),
    # Sentry endpoint for frontend errors
    path("sentry-debug/", trigger_error, name="sentry_debug"),
    # Redirection urls post-migration
    # TODO post-migration: remove at some point in the future (2022 ?)
    path(
        "fr/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="pages:home", permanent=True), name="old_home"),
                path("page/faq", RedirectView.as_view(url="/faq/", permanent=True), name="old_page_faq"),
                path(
                    "page/qui-sommes-nous",
                    RedirectView.as_view(url="/qui-sommes-nous/", permanent=True),
                    name="old_page_qui",
                ),
                path(
                    "itou/inclusion",
                    RedirectView.as_view(pattern_name="pages:decouvrir_inclusion", permanent=True),
                    name="old_page_inclusion",
                ),
                path(
                    "filiere/restauration",
                    RedirectView.as_view(pattern_name="pages:filiere_restauration", permanent=True),
                    name="old_page_filiere_restauration",
                ),
                path(
                    "filiere/recyclage",
                    RedirectView.as_view(pattern_name="pages:filiere_recyclage", permanent=True),
                    name="old_page_filiere_recyclage",
                ),
                path(
                    "contact/creer",
                    RedirectView.as_view(pattern_name="pages:contact", permanent=True),
                    name="old_page_contact",
                ),
                path(
                    "identification/",
                    RedirectView.as_view(pattern_name="auth:login", permanent=True),
                    name="old_signup",
                ),
                path(
                    "identification",
                    RedirectView.as_view(pattern_name="auth:login", permanent=True),
                    name="old_login_without_slash",
                ),
                path(
                    "inscription/",
                    RedirectView.as_view(pattern_name="auth:signup", permanent=True),
                    name="old_login",
                ),
                path(
                    "inscription",
                    RedirectView.as_view(pattern_name="auth:signup", permanent=True),
                    name="old_signup_without_slash",
                ),
                path(
                    "tableau-de-bord/profil-utilisateur/editer-a-propos-de-moi/",
                    RedirectView.as_view(pattern_name="dashboard:home", permanent=True),
                    name="old_dashboard_home",
                ),
                path(
                    "tableau-de-bord/profil-utilisateur/editer-a-propos-de-moi",
                    RedirectView.as_view(pattern_name="dashboard:home", permanent=True),
                    name="old_dashboard_home_without_slash",
                ),
                path(
                    "dashboard/directory/",
                    RedirectView.as_view(pattern_name="dashboard:home", permanent=True),
                    name="old_dashboard_siaes_home",
                ),
                path(
                    "dashboard/directory",
                    RedirectView.as_view(pattern_name="dashboard:home", permanent=True),
                    name="old_dashboard_siaes_home_without_slash",
                ),
                path(
                    "repertoire/siae/",
                    RedirectView.as_view(pattern_name="siae:search_results", permanent=True),
                    name="old_siae_search",
                ),
                path(
                    "repertoire/siae",
                    RedirectView.as_view(pattern_name="siae:search_results", permanent=True),
                    name="old_siae_search_without_slash",
                ),
                path(
                    "directory/<str:slug>/show/",
                    RedirectView.as_view(pattern_name="siae:detail", permanent=True),
                    name="old_siae_detail",
                ),  # <int:pk>
                path(
                    "directory/<str:slug>/show",
                    RedirectView.as_view(pattern_name="siae:detail", permanent=True),
                    name="old_siae_detail_without_slash",
                ),  # <int:pk>
                path(
                    "directory/<str:slug>/",
                    RedirectView.as_view(pattern_name="siae:detail", permanent=True),
                    name="old_siae_detail_without_show",
                ),  # <int:pk>
            ]
        ),
    ),
    # Flatpages (created in the admin)
    # path("", include("django.contrib.flatpages.urls")),
    path("<path:url>", PageView.as_view(), name="flatpage"),
    # Error pages
    path("403/", TemplateView.as_view(template_name="403.html"), name="403"),
    path("404/", TemplateView.as_view(template_name="404.html"), name="404"),
    path("500/", TemplateView.as_view(template_name="500.html"), name="500"),
]
