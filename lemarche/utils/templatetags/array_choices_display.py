from django import template
from django.utils.html import mark_safe

from lemarche.siaes import constants as siae_constants
from lemarche.utils.data import choice_array_to_string


register = template.Library()


@register.simple_tag
def array_choices_display(obj, field, output_format="string"):
    """Pretty rendering of ArrayField with choices."""

    choices_dict = dict()

    if field == "presta_type":
        choices_dict = dict(siae_constants.PRESTA_CHOICES)

    try:
        keys = obj.get(field, [])
    except:  # noqa
        keys = getattr(obj, field, [])

    values = choice_array_to_string(choices_dict, keys)

    # output format
    if output_format == "list":
        return values
    elif output_format == "li":
        return mark_safe("".join([f"<li>{elem_name}</li>" for elem_name in values]))
    elif output_format == "br":
        return mark_safe("<br />".join(values))
    else:  # "string"
        return ", ".join(values)
