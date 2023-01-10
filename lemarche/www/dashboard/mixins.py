from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender
from lemarche.users.models import User


"""
UserPassesTestMixin cannot be stacked
https://docs.djangoproject.com/en/4.0/topics/auth/default/#django.contrib.auth.mixins.UserPassesTestMixin.get_test_func
https://stackoverflow.com/a/60302594/4293684

How to have LoginRequiredMixin (redirects to next url if anonymous) + custom mixin ?
--> custom dispatch() method
"""


class LoginRequiredUserPassesTestMixin(UserPassesTestMixin):
    """
    Custom mixin that mimicks the LoginRequiredMixin behavior
    https://stackoverflow.com/a/59661739
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        return super().dispatch(request, *args, **kwargs)


class NotSiaeUserRequiredMixin(LoginRequiredUserPassesTestMixin):
    """
    Restrict access to non-SIAE users
    Where?
    - Tender create form
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.kind != User.KIND_SIAE)

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("tenders:list"))


class SiaeUserRequiredMixin(LoginRequiredUserPassesTestMixin):
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


class SiaeMemberRequiredMixin(LoginRequiredUserPassesTestMixin):
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


class SiaeNotMemberRequiredMixin(LoginRequiredUserPassesTestMixin):
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


class SiaeUserAndNotMemberRequiredMixin(LoginRequiredUserPassesTestMixin):
    """
    SiaeUserRequiredMixin + SiaeNotMemberRequiredMixin
    """

    def test_func(self):
        return SiaeUserRequiredMixin.test_func(self) and SiaeNotMemberRequiredMixin.test_func(self)

    def handle_no_permission(self):
        if SiaeUserRequiredMixin.test_func(self) and not SiaeNotMemberRequiredMixin.test_func(self):
            messages.add_message(self.request, messages.WARNING, "Vous êtes déjà rattaché à cette structure.")
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class FavoriteListOwnerRequiredMixin(LoginRequiredUserPassesTestMixin):
    """
    Restrict access to the "view FavoriteList" page to the FavoriteList's user
    """

    def test_func(self):
        user = self.request.user
        favorite_list_slug = self.kwargs.get("slug")
        return user.is_authenticated and (favorite_list_slug in user.favorite_lists.values_list("slug", flat=True))

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class TenderAuthorOrAdminRequiredMixin(LoginRequiredUserPassesTestMixin):
    """
    Restrict access to the Tender's author
    """

    def test_func(self):
        user = self.request.user
        tender_slug = self.kwargs.get("slug")
        return user.is_authenticated and (
            (tender_slug in user.tenders.values_list("slug", flat=True)) or (user.kind == user.KIND_ADMIN)
        )

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("tenders:list"))


class TenderAuthorOrAdminRequiredIfNotValidatedMixin(LoginRequiredUserPassesTestMixin):
    """
    If the Tender's status is not "validated", restrict access to the Tender's author (or Admin)
    """

    def test_func(self):
        # user = self.request.user
        tender_slug = self.kwargs.get("slug")
        tender = Tender.objects.get(slug=tender_slug)
        if not tender.status == tender_constants.STATUS_VALIDATED:
            return TenderAuthorOrAdminRequiredMixin.test_func(self)
        return True

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, "Vous n'avez pas accès à cette page.")
        return HttpResponseRedirect(reverse_lazy("pages:home"))
