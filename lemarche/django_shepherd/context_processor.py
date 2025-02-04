from django.core.exceptions import ObjectDoesNotExist

from lemarche.django_shepherd.models import UserGuide


def expose_guide_context(request):
    """
    DISPLAY_GUIDE is set to True if for the current url a display guide is found and the current user
    have not completed it yet
    """
    url = request.path.strip("/")
    try:
        user_guide = UserGuide.objects.get(url__contains=url)
    except ObjectDoesNotExist:
        display_guide = False
    else:
        display_guide = not user_guide.guided_users.filter(id=request.user.id).exists()
    return {"DISPLAY_GUIDE": display_guide}
