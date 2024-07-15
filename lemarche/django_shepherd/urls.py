from django.urls import path

from .views import UserGuideView


urlpatterns = [
    path("get_guide/<str:guide_name>/", UserGuideView.as_view(), name="get_guide"),
]
