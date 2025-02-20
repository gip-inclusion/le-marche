from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic.detail import BaseDetailView

from lemarche.django_shepherd.models import UserGuide


class StepViewedView(LoginRequiredMixin, BaseDetailView):
    queryset = UserGuide.objects.all()

    def get(self, request, *args, **kwargs):
        """Add the current user to the list of users that seen the guide"""
        self.get_object().guided_users.add(self.request.user)
        return HttpResponse(status=200)
