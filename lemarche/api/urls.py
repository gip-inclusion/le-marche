from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import routers

from lemarche.api.networks.views import NetworkViewSet
from lemarche.api.sectors.views import SectorViewSet
from lemarche.api.siaes.views import SiaeViewSet


router = routers.DefaultRouter()

router.register(r'siae', SiaeViewSet, basename='siae')
router.register(r'sectors', SectorViewSet, basename='sectors')
router.register(r'networks', NetworkViewSet, basename='networks')


urlpatterns = [
    # Additional API endpoints
    path("siaes/siret/<str:siret>/", SiaeViewSet.as_view({"get": "retrieve_by_siret"})),

    # Swagger / OpenAPI documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns += router.urls
