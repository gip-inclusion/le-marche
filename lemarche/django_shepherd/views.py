from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.detail import BaseDetailView

from lemarche.django_shepherd.models import UserGuide


class UserGuideView(View):
    def get(self, request, guide_slug):
        guide = UserGuide.objects.get(slug=guide_slug)
        steps = guide.steps.all()
        steps_data = [
            {
                "title": step.title,
                "text": step.text,
                "element": step.element,
                "position": step.position,
            }
            for step in steps
        ]
        return JsonResponse({"steps": steps_data})


class StepViewedView(BaseDetailView):
    queryset = UserGuide.objects.all()

    def get(self, request, *args, **kwargs):
        """Add the current user to the list of users that seen the guide"""
        self.get_object().guided_users.add(self.request.user)
        return HttpResponse(status=200)
