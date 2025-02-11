from django.urls import path

from lemarche.django_shepherd.views import StepViewedView


app_name = "django_shepherd"

urlpatterns = [
    path("viewed_guide/<int:pk>/", StepViewedView.as_view(), name="guide_viewed_view"),
]
