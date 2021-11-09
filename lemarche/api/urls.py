from django.urls import path
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import routers

from lemarche.api.networks.views import NetworkViewSet
from lemarche.api.perimeters.views import PerimeterAutocompleteViewSet, PerimeterKindViewSet, PerimeterViewSet
from lemarche.api.sectors.views import SectorViewSet
from lemarche.api.siaes.views import SiaeKindViewSet, SiaePrestaTypeViewSet, SiaeViewSet


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "api"

router = routers.DefaultRouter()
router.register(r"siae/kinds", SiaeKindViewSet, basename="siae-kinds")
router.register(r"siae/presta-types", SiaePrestaTypeViewSet, basename="siae-presta-types")
router.register(r"siae", SiaeViewSet, basename="siae")
router.register(r"sectors", SectorViewSet, basename="sectors")
router.register(r"networks", NetworkViewSet, basename="networks")
router.register(r"perimeters/kinds", PerimeterKindViewSet, basename="perimeter-kinds")
router.register(r"perimeters/autocomplete", PerimeterAutocompleteViewSet, basename="perimeters-autocomplete")
router.register(r"perimeters", PerimeterViewSet, basename="perimeters")

urlpatterns = [
    path("", TemplateView.as_view(template_name="api/home.html"), name="home"),
    # Additional API endpoints
    path("siae/slug/<str:slug>/", SiaeViewSet.as_view({"get": "retrieve_by_slug"}), name="siae-retrieve-by-slug"),
    path("siae/siret/<str:siret>/", SiaeViewSet.as_view({"get": "retrieve_by_siret"}), name="siae-retrieve-by-siret"),
    path(
        "siaes/siret/<str:siret>/",
        RedirectView.as_view(pattern_name="api:siae-retrieve-by-siret", permanent=True),
        name="old_api_siae_siret",
    ),
    # Swagger / OpenAPI documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]

urlpatterns += router.urls
