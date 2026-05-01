from django.urls import path

from lemarche.www.testimonials.views import TestimonialConfirmView, TestimonialSubmitView


app_name = "testimonials"

urlpatterns = [
    path("<uuid:token>/", TestimonialSubmitView.as_view(), name="submit"),
    path("<uuid:token>/merci/", TestimonialConfirmView.as_view(), name="confirm"),
]
