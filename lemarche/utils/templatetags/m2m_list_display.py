from django import template
from django.utils.encoding import force_str
from django.utils.html import mark_safe

from lemarche.siaes.models import Siae


register = template.Library()


@register.simple_tag
def m2m_list_display(obj, field, display_max=5, output_format="string"):
    """Pretty rendering of M2M fields."""

    if type(obj) == Siae:
        if field == "sectors":
            qs = obj.sectors.all()

    # get values
    values = list(qs)

    # get list of names
    values = [force_str(elem.name) for elem in values if elem.name != "Autre"]

    # filter number of displayed values
    if len(values) > display_max:
        values = values[:display_max]
        values.append("…")

    # output format
    if output_format == "list":
        return values
    elif output_format == "li":
        return mark_safe("".join([f"<li>{elem}</li>" for elem in values]))
    else:  # "string"
        return ", ".join(values)
