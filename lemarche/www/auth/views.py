from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from lemarche.users.models import User
from lemarche.utils.urls import get_safe_url
from lemarche.www.auth.forms import LoginForm, PasswordResetForm, SignupForm
from lemarche.www.auth.tasks import send_signup_notification_email, send_welcome_email


class LoginView(auth_views.LoginView):
    template_name = "auth/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True
    # success_url = settings.LOGIN_REDIRECT_URL  # see get_success_url() below

    def get(self, request, *args, **kwargs):
        """Check if there is any custom message to display."""
        message = request.GET.get("message", None)
        # Users need to be logged in to download the search results in CSV
        if message == "login-to-download":
            messages.add_message(request, messages.INFO, "Vous devez être connecté pour télécharger la liste.")
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to next_url if there is a next param."""
        success_url = super().get_success_url()
        next_url = self.request.GET.get("next", None)
        # sanitize next_url
        if next_url:
            safe_url = get_safe_url(self.request, param_name="next")
            if safe_url:
                success_url = safe_url
        return success_url


class SignupView(SuccessMessageMixin, CreateView):
    template_name = "auth/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("pages:home")
    success_message = "Inscription validée !"  # see get_success_message() below

    def form_valid(self, form):
        """
        - send a welcome email to the user
        - send a notification email to the staff
        """
        user = form.save()
        send_welcome_email(user)
        send_signup_notification_email(user)
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        success_message = super().get_success_message(cleaned_data)
        success_message += f" Vous pouvez maintenant vous <a href=\"{reverse_lazy('auth:login')}\">connecter</a>."
        if cleaned_data["kind"] == User.KIND_SIAE:
            success_message += " L'ajout de votre structure se fera ensuite dans votre espace utilisateur."
        return success_message


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "auth/password_reset.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("auth:password_reset_sent")  # see get_success_url() below
    email_template_name = "auth/password_reset_email_body.html"
    subject_template_name = "auth/password_reset_email_subject.txt"

    def get_success_url(self):
        success_url = super().get_success_url()
        user_email = self.request.POST.get("email")
        return f"{success_url}?email={user_email}"
