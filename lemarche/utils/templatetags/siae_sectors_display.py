from django import template
from django.utils.encoding import force_str
from django.utils.html import mark_safe


register = template.Library()


@register.simple_tag
def siae_sectors_display(siae, display_max=5, current_search_query="", output_format="string"):
    """Pretty rendering of M2M fields."""

    qs = siae.sectors.all()

    # get values
    values = list(qs)

    # if the search query contains sectors, filter values on these sectors
    if "sectors=" in current_search_query:
        values = [elem for elem in values if elem.slug in current_search_query]

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
