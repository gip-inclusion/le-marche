from django.views.generic import CreateView, FormView
from django.contrib.auth import views as auth_views
from django.urls import reverse, reverse_lazy
from django.contrib import messages

from lemarche.www.auth.tasks import send_signup_notification_email
from lemarche.www.auth.forms import SignupForm, PasswordResetForm


class SignupView(CreateView):
    template_name = "auth/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        """Send a notification email to the team."""
        user = form.save()
        send_signup_notification_email(user)
        messages.success(self.request, "Inscription validée !")
        return super().form_valid(form)


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "auth/password_reset.html"
    form_class = PasswordResetForm
    # success_url = reverse_lazy("password_reset_sent")
    email_template_name = "auth/password_reset_email.html"
    subject_template_name = "auth/password_reset_subject.txt"

    def get_success_url(self):
        success_url = reverse("password_reset_sent")
        user_email = self.request.POST.get("email")
        return f"{success_url}?email={user_email}"
