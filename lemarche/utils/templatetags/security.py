import hashlib

from django import template


register = template.Library()

#
# {{ "some identifier"|hash_value }}


@register.filter(name="hash_value")
def hash_value(value):
    return hashlib.sha256(str(value).encode()).hexdigest()
