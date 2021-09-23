from django import template
from django.utils.encoding import force_str

from lemarche.siaes.models import Siae


register = template.Library()


@register.simple_tag
def m2m_list_display(obj, field, display_max=5):
    """Pretty rendering of M2M fields."""

    if type(obj) == Siae:
        if field == "sectors":
            qs = obj.sectors.all()

    values = [force_str(elem.name) for elem in list(qs) if elem.name != "Autre"]
    values_to_string = ", ".join(values[:display_max])
    if len(values) > display_max:
        values_to_string += ", ..."

    return values_to_string
