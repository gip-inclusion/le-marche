from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy


class NonOnboardedRedirectMiddleware:
    """Users that have not yet been onboarded are redirected to specific pages"""

    allowed_views = [reverse_lazy("auth:booking-meeting-view")]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and not request.user.is_onboarded:
            if request.path not in self.allowed_views:
                return redirect(reverse("auth:booking-meeting-view"))
        return None
