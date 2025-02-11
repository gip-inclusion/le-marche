from django.core.exceptions import ObjectDoesNotExist

from lemarche.django_shepherd.models import UserGuide


def expose_guide_context(request):
    """
    DISPLAY_GUIDE is set to True if for the current url a display guide is found and the current user
    have not completed it yet.
    DISPLAY_GUIDE_PAYLOAD is when a guide is found the data of all the steps of the guide
    """
    url_path = request.path.strip("/")
    try:
        user_guide = UserGuide.objects.get(url_path=url_path)
    except ObjectDoesNotExist:  # No guide found on this url
        display_guide_flag = False
        display_guide_payload = None
        display_guide_pk = None
    else:  # A guide has been found
        user_had_viewed = user_guide.guided_users.filter(id=request.user.id).exists()
        if request.user.is_anonymous or user_had_viewed:
            # Current user has already seen this guide, or is anonymous
            display_guide_flag = False
            display_guide_payload = None
            display_guide_pk = None
        else:  # Current user has not yet seen this guide
            display_guide_flag = not user_had_viewed
            steps = user_guide.steps.all()
            steps_data = [
                {
                    "title": step.title,
                    "text": step.text,
                    "element": step.element,
                    "position": step.position,
                }
                for step in steps
            ]
            display_guide_payload = {"steps": steps_data}
            display_guide_pk = user_guide.pk
    return {
        "DISPLAY_GUIDE_FLAG": display_guide_flag,
        "DISPLAY_GUIDE_PK": display_guide_pk,
        "DISPLAY_GUIDE_PAYLOAD": display_guide_payload,
    }
