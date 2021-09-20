from django.views.generic import CreateView
from django.urls import reverse_lazy

from lemarche.www.auth.forms import SignupForm


class SignupView(CreateView):
    template_name = "auth/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("home")
