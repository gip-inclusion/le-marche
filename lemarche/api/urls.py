from django.urls import path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import routers

from lemarche.api.networks.views import NetworkViewSet
from lemarche.api.sectors.views import SectorViewSet
from lemarche.api.siaes.views import SiaeViewSet


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "api"

router = routers.DefaultRouter()
router.register(r"siae", SiaeViewSet, basename="siae")
router.register(r"sectors", SectorViewSet, basename="sectors")
router.register(r"networks", NetworkViewSet, basename="networks")

urlpatterns = [
    path("", TemplateView.as_view(template_name="api/home.html"), name="home"),
    # Additional API endpoints
    path("siaes/siret/<str:siret>/", SiaeViewSet.as_view({"get": "retrieve_by_siret"})),
    # Swagger / OpenAPI documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]

urlpatterns += router.urls
