from django.urls import path
from c4_directory import views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('siaes/', views.siae_list),
    path('siae/<int:key>/', views.siae_detail),
    # YOUR PATTERNS
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='OpenAPI'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
