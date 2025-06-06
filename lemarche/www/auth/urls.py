from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from lemarche.www.auth.views import CustomLoginView, CustomSignupView, MeetingCalendarView, PasswordResetView


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "auth"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="account_login"),
    path("signup/", CustomSignupView.as_view(), name="account_signup"),
    path("rendez-vous/", MeetingCalendarView.as_view(), name="booking-meeting-view"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_sent.html"),
        name="password_reset_sent",
    ),  # name="password_reset_done"
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html", success_url=reverse_lazy("auth:password_reset_complete")
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
