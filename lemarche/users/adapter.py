from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse_lazy

from lemarche.users.models import User
from lemarche.utils.urls import get_safe_url


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
