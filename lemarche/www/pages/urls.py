from django.urls import path
from lemarche.www.pages import views

# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "pages"

urlpatterns = [
    path("cest-quoi-linclusion", views.inclusion, name="pages-inclusion"),
]
