from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from lemarche.users.models import User


class SiaeUserRequiredMixin(UserPassesTestMixin):
    """
    Restrict access to specific users: Siae & Admin
    Where?
    - "adopt Siae" workflow
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.kind in [User.KIND_SIAE, User.KIND_ADMIN])

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class SiaeMemberRequiredMixin(UserPassesTestMixin):
    """
    Restrict access to Siae's users
    Where?
    - "edit Siae" page
    """

    def test_func(self):
        user = self.request.user
        siae_slug = self.kwargs.get("slug")
        return user.is_authenticated and (siae_slug in user.siaes.values_list("slug", flat=True))

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class SiaeNotMemberRequiredMixin(UserPassesTestMixin):
    """
    Restrict access to users who do not belong to the Siae
    Where?
    - "adopt Siae" workflow
    """

    def test_func(self):
        user = self.request.user
        siae_slug = self.kwargs.get("slug")
        return user.is_authenticated and not (siae_slug in user.siaes.values_list("slug", flat=True))

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, "Vous êtes déjà rattaché à cette structure.")
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class SiaeUserAndNotMemberRequiredMixin(UserPassesTestMixin):
    """
    SiaeUserRequiredMixin + SiaeNotMemberRequiredMixin
    https://stackoverflow.com/a/60302594/4293684
    """

    def test_func(self):
        return SiaeUserRequiredMixin.test_func(self) and SiaeNotMemberRequiredMixin.test_func(self)

    def handle_no_permission(self):
        if SiaeUserRequiredMixin.test_func(self) and not SiaeNotMemberRequiredMixin.test_func(self):
            messages.add_message(self.request, messages.WARNING, "Vous êtes déjà rattaché à cette structure.")
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class FavoriteListOwnerRequiredMixin(UserPassesTestMixin):
    """
    Restrict access to the "view FavoriteList" page to the FavoriteList's user
    """

    def test_func(self):
        user = self.request.user
        favorite_list_slug = self.kwargs.get("slug")
        return user.is_authenticated and (favorite_list_slug in user.favorite_lists.values_list("slug", flat=True))

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))
