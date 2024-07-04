from django import template


register = template.Library()


@register.simple_tag
def process_dict(**kwargs):
    return kwargs
