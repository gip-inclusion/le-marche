from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from lemarche.users.models import User


class SiaeUserRequiredMixin(UserPassesTestMixin):
    """
    Restrict access to the "adopt Siae" workflow to specific users: Siae & Admin
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.kind in [User.KIND_SIAE, User.KIND_ADMIN]

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class SiaeOwnerRequiredMixin(UserPassesTestMixin):
    """
    Restrict access to the "edit Siae" page to the Siae's users
    """

    def test_func(self):
        user = self.request.user
        siae_slug = self.kwargs.get("slug")
        return user.is_authenticated and siae_slug in user.siaes.values_list("slug", flat=True)

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))
