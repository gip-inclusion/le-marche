from django.http import JsonResponse
from django.views import View

from .models import UserGuide


class UserGuideView(View):
    def get(self, request, guide_name):
        guide = UserGuide.objects.get(name=guide_name)
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
