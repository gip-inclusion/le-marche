from django import template


register = template.Library()


@register.filter
def fr_number(value):
    """Format a number with French thousands separator (narrow no-break space)."""
    if value is None or value == "":
        return ""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return value
