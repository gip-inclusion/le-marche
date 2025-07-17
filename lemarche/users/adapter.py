from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.urls import reverse_lazy

from lemarche.users.models import User
from lemarche.utils.emails import add_to_contact_list
from lemarche.utils.urls import get_safe_url
from lemarche.www.auth.tasks import send_signup_notification_email


class LeMarcheAccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        """
        This redirect is called only if the user already has a verifier email.
        If not, upon login the user will be redirected the the page asking to check its email.
        This method could work out of the box with the CustomLoginView and overridden get_success_url()
        """
        success_url = super().get_login_redirect_url(request)
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

    def get_signup_redirect_url(self, request):
        success_url = super().get_signup_redirect_url(request)

        if settings.GOOGLE_AGENDA_IFRAME_URL and self.request.user.kind == User.KIND_BUYER:
            success_url = reverse_lazy("auth:booking-meeting-view")
        next_url = self.request.GET.get("next", None)
        # sanitize next_url
        if next_url:
            safe_url = get_safe_url(self.request, param_name="next")
            if safe_url:
                return safe_url
        elif self.request.POST.get("kind") == User.KIND_SIAE:
            return reverse_lazy("dashboard:home")

        return success_url

    def save_user(self, request, user, form, commit=True):
        """
        Add extra data from the form to 'extra_data' JSON field
        """
        user = super().save_user(request, user, form, commit=False)

        # Hard to understand allauth logic, this code could also be in in the .save() method of the SignUpForm
        # But it may be better to regroup all the logic here, it would be as ugly in .save()
        user.kind = form.cleaned_data.get("kind")
        user.first_name = form.cleaned_data.get("first_name")
        user.last_name = form.cleaned_data.get("last_name")
        user.phone = form.cleaned_data.get("phone")
        user.buyer_kind_detail = form.cleaned_data.get("buyer_kind_detail")
        user.company_name = form.cleaned_data.get("company_name")
        user.position = form.cleaned_data.get("position")
        user.partner_kind = form.cleaned_data.get("partner_kind")
        user.accept_rgpd = form.cleaned_data.get("accept_rgpd")
        user.accept_survey = form.cleaned_data.get("accept_survey")
        user.accept_share_contact_to_external_partners = form.cleaned_data.get(
            "accept_share_contact_to_external_partners"
        )

        extra_data = {}
        if form.cleaned_data.get("nb_of_inclusive_provider_last_year"):
            extra_data["nb_of_inclusive_provider_last_year"] = form.cleaned_data.get(
                "nb_of_inclusive_provider_last_year"
            )

        if form.cleaned_data.get("nb_of_handicap_provider_last_year"):
            extra_data["nb_of_handicap_provider_last_year"] = form.cleaned_data.get(
                "nb_of_handicap_provider_last_year"
            )

        user.extra_data = extra_data

        if commit:
            user.save()
            user.sectors.set(form.cleaned_data.get("sectors"))
            # add to Brevo list (to send welcome email + automation)
            add_to_contact_list(user, "signup")
            # signup notification email for the team
            send_signup_notification_email(user)

        return user
