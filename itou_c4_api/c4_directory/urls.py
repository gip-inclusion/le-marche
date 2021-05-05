from django.urls import path
from c4_directory import views

urlpatterns = [
    path('siaes/', views.siae_list),
    #path('siaes/<int:id>/', views.siae_detail),
]
