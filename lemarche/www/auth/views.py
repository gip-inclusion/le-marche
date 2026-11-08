from allauth.account.views import ConfirmEmailView, LoginView, SignupView
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html

from lemarche.users.models import User
from lemarche.www.auth.forms import CustomLoginForm, CustomSignupForm, PasswordResetForm


class CustomLoginView(LoginView):
    template_name = "account/login.html"
    form_class = CustomLoginForm

    def get_context_data(self, **kwargs):
        """
        - Get next param to append to the signup url
        Note: do not expose any account-specific state here (e.g. "user without password"),
        to avoid user enumeration through the login form.
        """
        context = super().get_context_data(**kwargs)
        next_url = self.request.GET.get("next", None)
        if next_url:
            context["next_param"] = f"?next={next_url}"
        return context


class CustomSignupView(SignupView):
    template_name = "account/signup.html"
    form_class = CustomSignupForm


class CustomConfirmEmailView(ConfirmEmailView):
    def post(self, *args, **kwargs):
        """
        Once the address is confirmed (the new user is then logged in, email verification being mandatory),
        invite SIAE users who don't have a structure yet to add one.
        """
        response = super().post(*args, **kwargs)
        email_address = self.object.email_address
        email_address.refresh_from_db()
        user = email_address.user
        if email_address.verified and user.kind == User.KIND_SIAE and not user.has_siae:
            messages.success(
                self.request,
                format_html(
                    "Vous pouvez maintenant ajouter votre structure en cliquant sur "
                    '<a href="{}">Ajouter une structure</a>.',
                    reverse("dashboard_siaes:siae_search_by_siret"),
                ),
            )
        return response

    def logout_other_user(self, confirmation):
        """
        allauth logs out the current user when the confirmation link belongs to another account,
        including on GET: any (cross-site) link would log out the user.
        Only do it on POST (CSRF protected), i.e. once the user explicitly confirmed.
        """
        if self.request.method == "POST":
            super().logout_other_user(confirmation)


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
