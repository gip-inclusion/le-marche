from django.urls import path

from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from lemarche.api.siaes.views import SiaeViewSet, SectorViewSet


router = routers.DefaultRouter()

router.register(r'siaes', SiaeViewSet, basename='siaes')
router.register(r'sectors', SectorViewSet, basename='sectors')


urlpatterns = [
    # Additional API endpoints
    path("siaes/siret/<str:siret>/", SiaeViewSet.as_view({"get": "retrieve_by_siret"})),

    # Swagger / OpenAPI documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns += router.urls
