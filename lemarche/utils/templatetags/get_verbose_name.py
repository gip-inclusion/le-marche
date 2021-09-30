from django import template


register = template.Library()


@register.simple_tag
def get_verbose_name(object, field_name=None):
    if field_name:
        return object._meta.get_field(field_name).verbose_name
    else:
        return object._meta.verbose_name
