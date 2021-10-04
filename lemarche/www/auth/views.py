from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from lemarche.utils.urls import get_safe_url
from lemarche.www.auth.forms import PasswordResetForm, SignupForm
from lemarche.www.auth.tasks import send_signup_notification_email


class LoginView(auth_views.LoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True
    # success_url = settings.LOGIN_REDIRECT_URL

    def get(self, request, *args, **kwargs):
        message = request.GET.get("message", None)
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
    success_message = "Inscription validée ! Vous pouvez maintenant vous connecter."

    def form_valid(self, form):
        """Send a notification email to the team."""
        user = form.save()
        send_signup_notification_email(user)
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        success_message = super().get_success_message(cleaned_data)
        if cleaned_data["kind"] == "SIAE":
            success_message += " L'ajout de votre structure se fera ensuite dans votre espace utilisateur."
        return success_message


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "auth/password_reset.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("auth:password_reset_sent")
    email_template_name = "auth/password_reset_email_body.html"
    subject_template_name = "auth/password_reset_email_subject.txt"

    def get_success_url(self):
        success_url = super().get_success_url()
        user_email = self.request.POST.get("email")
        return f"{success_url}?email={user_email}"
