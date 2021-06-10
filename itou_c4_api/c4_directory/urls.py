from itou_c4_api.c4_directory import views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import routers


# Basic idea is to use hyperlinkedmodelserializer and viewsets
# But unclear documentation and confusing error messages did
# not allow it to work, yet.
router = routers.DefaultRouter()
router.register(r"hypersiaes", views.SiaesViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    # path('siaes/', views.siae_list),
    # path('siae/<int:key>', views.siae_detail, name='siae-detail'),
    path("secteurs/", views.sector_list),
    path("secteur/<str:key>", views.sector_detail),
    # YOUR PATTERNS
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="OpenAPI"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
