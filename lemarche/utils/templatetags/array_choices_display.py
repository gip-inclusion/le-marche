from django import template
from django.utils.encoding import force_str

from lemarche.siaes import constants as siae_constants


register = template.Library()


@register.simple_tag
def array_choices_display(obj, field):
    """Pretty rendering of ArrayField with choices."""

    choices_dict = dict()

    if field == "presta_type":
        choices_dict = dict(siae_constants.PRESTA_CHOICES)

    try:
        keys = obj.get(field, [])
    except:  # noqa
        keys = getattr(obj, field, [])

    values = [force_str(choices_dict.get(key, "")) for key in (keys or [])]
    return ", ".join(filter(None, values))
