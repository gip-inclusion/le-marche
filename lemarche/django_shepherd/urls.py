from django.urls import path

from .views import StepViewedView, UserGuideView


urlpatterns = [
    path("get_guide/<slug:guide_slug>/", UserGuideView.as_view(), name="get_guide"),
    path("viewed_guide/<slug:slug>/", StepViewedView.as_view(), name="guide_viewed_view"),
]
