from django import template
from django.utils.encoding import force_str
from django.utils.html import mark_safe


register = template.Library()


@register.simple_tag
def siae_sectors_display(object, display_max=5, current_search_query="", output_format="string"):
    """
    Pretty rendering of M2M fields.
    - object can be SectorGroup, SiaeActivity...
    """

    values = []
    for sector in object.sectors.all():
        values.append({"slug": sector.slug, "name": sector.name})

    # if the search query contains sectors, filter values on these sectors
    if "sectors=" in current_search_query:
        values = [elem for elem in values if elem["slug"] in current_search_query]

    # get list of names
    values = [force_str(elem["name"]) for elem in values if elem["name"] != "Autre"]

    # filter number of displayed values
    if len(values) > display_max:
        values = values[:display_max]
        values.append("…")

    # output format
    if output_format == "list":
        return values
    elif output_format == "li":
        return mark_safe("".join([f"<li>{elem_name}</li>" for elem_name in values]))
    else:  # "string"
        return ", ".join(values)


@register.inclusion_tag("utils/templatetags/siae_sectors_display.html")
def siae_sector_groups_display(object, display_max=5, current_sector_groups=[]):
    """
    Pretty rendering of M2M field SectorGroup for Siae.
    """

    # to avoid duplicates and display current search values first
    seen_slugs = set()

    current_values = []
    # Add sector groups from current_sector_groups if they are in object's activities
    for sector_group in current_sector_groups:
        if any(activity.sector_group.slug == sector_group.slug for activity in object.activities.all()):
            if sector_group.slug not in seen_slugs:
                current_values.append(sector_group.name)
                seen_slugs.add(sector_group.slug)

    values = []

    # Add remaining sector groups from object's activities
    for activity in object.activities.all():
        if activity.sector.group.slug not in seen_slugs:
            values.append(activity.sector.group.name)
            seen_slugs.add(activity.sector.group.slug)

    # alphabetical order here to avoid N+1 queries
    values = sorted(values)

    # filter number of displayed values
    groups_count = len(seen_slugs)
    if groups_count > display_max:
        display_max_values = display_max - len(current_values)
        if display_max_values > 0:
            values = values[:display_max_values]
        else:
            values = []
        values.append(f"+{groups_count - display_max}")

    return {"current_search_sector_groups": sorted(current_values), "sector_groups": values}
