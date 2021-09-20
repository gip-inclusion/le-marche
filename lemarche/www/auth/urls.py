from django.urls import path
from django.contrib.auth import views as auth_views

from lemarche.www.auth.views import SignupView


urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="auth/logged_out.html"), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
]
