from allauth.account.views import LoginView, SignupView
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from lemarche.cms.snippets import Paragraph
from lemarche.users.models import User
from lemarche.www.auth.forms import CustomLoginForm, CustomSignupForm, PasswordResetForm


class CustomLoginView(LoginView):
    template_name = "account/login.html"
    form_class = CustomLoginForm

    def get_context_data(self, **kwargs):
        """
        - Show post-migration message to existing users (they need to reset their password).
        - Get next param to append to the signup url
        """
        context = super().get_context_data(**kwargs)
        email = self.request.POST.get("login", "")
        if email:
            user = User.objects.filter(email=email.lower()).first()
            if user:
                context["new_user_without_password"] = True if not getattr(user, "password", "") else False
        next_url = self.request.GET.get("next", None)
        if next_url:
            context["next_param"] = f"?next={next_url}"
        return context


class CustomSignupView(SuccessMessageMixin, SignupView):
    template_name = "account/signup.html"
    form_class = CustomSignupForm

    def get_success_message(self, cleaned_data):
        """Show detailed welcome message to SIAE."""
        success_message = super().get_success_message(cleaned_data)

        if cleaned_data["kind"] == User.KIND_BUYER and settings.GOOGLE_AGENDA_IFRAME_URL:
            return None  # Do not add message for BUYER that need meeting
        elif cleaned_data["kind"] == User.KIND_SIAE:
            success_message += mark_safe(
                "<br />Vous pouvez maintenant ajouter votre structure en cliquant sur "
                f"<a href=\"{reverse_lazy('dashboard_siaes:siae_search_by_siret')}\">Ajouter une structure</a>."
            )

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


class MeetingCalendarView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "auth/meeting_calendar.html"

    def test_func(self):
        """Do not display for already onboarded users"""
        if self.request.user.is_onboarded:
            return False
        return True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["wagtail_paragraph"] = Paragraph.objects.get(slug="rdv-signup")
        ctx["wagtail_contact"] = Paragraph.objects.get(slug="rdv-contact")
        ctx["agenda_iframe_url"] = settings.GOOGLE_AGENDA_IFRAME_URL
        return ctx
