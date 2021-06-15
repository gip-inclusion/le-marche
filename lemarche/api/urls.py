from lemarche.api import views
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


# Basic idea is to use hyperlinkedmodelserializer and viewsets
# But unclear documentation and confusing error messages did
# not allow it to work, yet.

urlpatterns = [
    path("siaes/", views.SiaeList.as_view()),
    path("siaes/<int:pk>/", views.SiaeDetail.as_view()),
    # path("api/", include(router.urls)),
    # path('siaes/', views.siae_list),
    # path('siae/<int:key>', views.siae_detail, name='siae-detail'),
    path("secteurs/", views.SectorList.as_view()),
    path("secteurs/<str:pk>", views.SectorDetail.as_view()),
    # YOUR PATTERNS
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="OpenAPI"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
