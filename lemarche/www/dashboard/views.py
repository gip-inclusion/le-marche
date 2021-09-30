from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView


class DashboardHomeView(DetailView):
    template_name = "dashboard/home.html"
    context_object_name = "user"

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super().get(request, args, kwargs)

    def get_object(self):
        return self.request.user
