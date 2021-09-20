from django.urls import path
from django.contrib.auth import views as auth_views

from lemarche.www.auth.views import SignupView, PasswordResetView


urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="auth/logged_out.html"), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/sent/", auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_sent.html"), name="password_reset_sent"),  # name="password_reset_done"
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name="password_reset_complete"),
]
