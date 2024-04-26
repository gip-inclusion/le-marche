from django.conf import settings
from django.urls import reverse_lazy

from lemarche.users.models import User


def home_page(request):
    """
    Put things into the context to make them available in templates.
    https://docs.djangoproject.com/en/4.2/ref/templates/api/#using-requestcontext
    """

    home_page = reverse_lazy("wagtail_serve", args=("",))
    if request.user.is_authenticated and request.user.kind == User.KIND_SIAE:
        home_page = settings.SIAE_HOME_PAGE

    return {"HOME_PAGE_PATH": home_page}
