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
