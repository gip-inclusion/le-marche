from django.urls import path
from lemarche.www.home import views

# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "home"

urlpatterns = [
    path("", views.home, name="hp"),
    # TODO: Add sentry
    # path("sentry-debug/", views.trigger_error, name="sentry_debug"),
]
