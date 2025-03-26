from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, TemplateView

from lemarche.cms.snippets import Paragraph
from lemarche.users.models import User
from lemarche.utils.emails import add_to_contact_list
from lemarche.utils.urls import get_safe_url
from lemarche.www.auth.forms import LoginForm, PasswordResetForm, SignupForm
from lemarche.www.auth.tasks import send_signup_notification_email


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
        if message == "login-to-favorite":
            messages.add_message(request, messages.INFO, "Vous devez être connecté pour créer des listes d'achats.")
        if message == "login-to-display-contacts":
            messages.add_message(request, messages.INFO, "Vous devez être connecté pour afficher les coordonnées.")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        - Show post-migration message to existing users (they need to reset their password).
        - Get next param to append to the signup url
        """
        context = super().get_context_data(**kwargs)
        email = self.request.POST.get("username", "")
        if email:
            user = User.objects.filter(email=email.lower()).first()
            if user:
                context["new_user_without_password"] = True if not getattr(user, "password", "") else False
        next_url = self.request.GET.get("next", None)
        if next_url:
            context["next_param"] = f"?next={next_url}"
        return context

    def get_success_url(self):
        """
        Redirect to:
        - next_url if there is a next param
        - or dashboard if SIAE
        """
        success_url = super().get_success_url()
        next_url = self.request.GET.get("next", None)
        # sanitize next_url
        if next_url:
            safe_url = get_safe_url(self.request, param_name="next")
            if safe_url:
                return safe_url
        elif self.request.user.kind == User.KIND_SIAE:
            return reverse_lazy("dashboard:home")
        elif self.request.user.kind == User.KIND_BUYER:
            return reverse_lazy("siae:search_results")
        return success_url


class SignupView(SuccessMessageMixin, CreateView):
    template_name = "auth/signup.html"
    form_class = SignupForm
    success_message = "Inscription validée !"  # see get_success_message() below

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.skip_meeting = self.request.GET.get("skip_meeting", None)

    def form_valid(self, form):
        """
        - send a welcome email to the user
        - send a notification email to the staff
        - login the user automatically
        - track signup
        """
        # User will be considered as onboarded when an admin will manually set it as onboarded
        # If no google agenda url, the functionality is disabled
        if form.instance.kind == User.KIND_BUYER and settings.GOOGLE_AGENDA_IFRAME_URL and not self.skip_meeting:
            form.instance.is_onboarded = False
        user = form.save()
        # add to Brevo list (to send welcome email + automation)
        add_to_contact_list(user, "signup")
        # signup notification email for the team
        send_signup_notification_email(user)
        # login the user
        user = authenticate(username=form.cleaned_data["email"], password=form.cleaned_data["password1"])
        login(self.request, user)
        # response
        if form.cleaned_data["kind"] == User.KIND_BUYER and settings.GOOGLE_AGENDA_IFRAME_URL:
            pass  # Do not add message for BUYER that need meeting
        else:
            messages.add_message(self.request, messages.SUCCESS, self.get_success_message(form.cleaned_data))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """
        Redirect to:
        - next_url if there is a next param
        - or dashboard if SIAE
        """
        if settings.GOOGLE_AGENDA_IFRAME_URL and self.request.user.kind == User.KIND_BUYER and not self.skip_meeting:
            success_url = reverse_lazy("auth:booking-meeting-view")
        else:
            success_url = reverse_lazy("wagtail_serve", args=("",))
        next_url = self.request.GET.get("next", None)
        # sanitize next_url
        if next_url:
            safe_url = get_safe_url(self.request, param_name="next")
            if safe_url:
                return safe_url
        elif self.request.POST.get("kind") == User.KIND_SIAE:
            return reverse_lazy("dashboard:home")
        return success_url

    def get_success_message(self, cleaned_data):
        """Show detailed welcome message to SIAE."""
        success_message = super().get_success_message(cleaned_data)
        if cleaned_data["kind"] == User.KIND_SIAE:
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
