from django.urls import path

from lemarche.www.dashboard.views import (
    DashboardHomeView,
    DisabledEmailEditView,
    InclusivePotentialAnalysisView,
    InclusivePurchaseStatsDashboardView,
    ProfileEditView,
    SlugMappingValidationView,
    inclusive_potential_excel_export,
    inclusive_potential_excel_template,
)


app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("modifier/", ProfileEditView.as_view(), name="profile_edit"),
    path("notifications/", DisabledEmailEditView.as_view(), name="notifications_edit"),
    path("part-achat-inclusif/", InclusivePurchaseStatsDashboardView.as_view(), name="inclusive_purchase_stats"),
    path("analyse-potentiel-inclusif/", InclusivePotentialAnalysisView.as_view(), name="inclusive_potential_analysis"),
    path(
        "analyse-potentiel-inclusif/modele-excel/",
        inclusive_potential_excel_template,
        name="inclusive_potential_analysis_template",
    ),
    path(
        "analyse-potentiel-inclusif/export-excel/",
        inclusive_potential_excel_export,
        name="inclusive_potential_analysis_export",
    ),
    path(
        "analyse-potentiel-inclusif/validation-matching/",
        SlugMappingValidationView.as_view(),
        name="slug_mapping_validation",
    ),
    # FavoriteList
    # see dashboard_favorites/urls.py
    # Network
    # see dashboard_networks/urls.py
    # Adopt Siae, Edit Siae & Siae Users
    # see dashboard_siaes/urls.py
]
