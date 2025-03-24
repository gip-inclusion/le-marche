from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from sesame.utils import get_user as sesame_get_user

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
        siae_slug = self.kwargs.get("siae_slug") or self.kwargs.get("slug")
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
        return user.is_authenticated and siae_slug not in user.siaes.values_list("slug", flat=True)

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


class NetworkMemberRequiredMixin(LoginRequiredUserPassesTestMixin):
    """
    Restrict access to Network's users
    """

    def test_func(self):
        user = self.request.user
        network_slug = self.kwargs.get("slug")
        return user.is_authenticated and user.partner_network and user.partner_network.slug == network_slug

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))


class TenderAuthorOrAdminRequiredMixin(LoginRequiredUserPassesTestMixin):
    """
    Restrict access to the Tender's author (or Admin)
    """

    def test_func(self):
        user = self.request.user
        tender_slug = self.kwargs.get("slug")
        return user.is_authenticated and (
            (tender_slug in user.tenders.values_list("slug", flat=True)) or (user.kind == user.KIND_ADMIN)
        )

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("tenders:list"))


class TenderAuthorOrAdminRequiredIfNotSentMixin(UserPassesTestMixin):
    """
    If the Tender's status is not "sent", restrict access to the Tender's author (or Admin)
    """

    def test_func(self):
        # user = self.request.user
        tender_slug = self.kwargs.get("slug")
        tender = get_object_or_404(Tender.objects.all(), slug=tender_slug)
        if tender.status != tender_constants.STATUS_SENT:
            return TenderAuthorOrAdminRequiredMixin.test_func(self)
        return True

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, "Vous n'avez pas accès à cette page.")
        return HttpResponseRedirect(reverse_lazy("wagtail_serve", args=("",)))


class SiaeUserRequiredOrSiaeIdParamMixin(UserPassesTestMixin):
    def test_func(self):
        """Authorize authenticated SIAE or numeric siae id"""
        siae_id = self.request.GET.get("siae_id", None)

        if (self.request.user.is_authenticated and self.request.user.kind == User.KIND_SIAE) or (
            siae_id and siae_id.isnumeric()
        ):
            return True

    def handle_no_permission(self):
        return HttpResponseForbidden()


class SesameTokenRequiredUserPassesTestMixin(UserPassesTestMixin):
    """
    Custom mixin that checks that a valid django-sesame token is passed
    """

    def dispatch(self, request, *args, **kwargs):
        user = sesame_get_user(self.request)
        if not user:
            return HttpResponseForbidden()
        # add user to request
        request.user = user
        return super().dispatch(request, *args, **kwargs)


class SesameTenderAuthorRequiredMixin(SesameTokenRequiredUserPassesTestMixin):
    """
    Restrict access to the Tender's author
    """

    def test_func(self):
        tender_slug = self.kwargs.get("slug")
        return tender_slug in self.request.user.tenders.values_list("slug", flat=True)

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("tenders:detail", args=[self.kwargs.get("slug")]))


class SesameSiaeMemberRequiredMixin(SesameTokenRequiredUserPassesTestMixin):
    """
    Restrict access to the Tender's author
    """

    def test_func(self):
        siae_slug = self.kwargs.get("siae_slug") or self.kwargs.get("slug")
        return siae_slug in self.request.user.siaes.values_list("slug", flat=True)

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy("dashboard:home"))
