from django.urls import path
from c4_directory import views

urlpatterns = [
    path('siaes/', views.siae_list),
    path('siae/<int:key>/', views.siae_detail),
]
