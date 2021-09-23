# https://github.com/betagouv/itou/blob/master/itou/utils/templatetags/url_add_query.py
# https://github.com/MTES-MCT/aides-territoires/blob/master/src/core/templatetags/pagination.py

from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def url_add_query(context, **kwargs):
    """
    Link to a page without losing existing GET parameters.
    """
    querydict = context["request"].GET
    mutable_querydict = querydict.copy()
    for item in kwargs:
        mutable_querydict[item] = str(kwargs[item])
    link = "?{}".format(mutable_querydict.urlencode())
    return link
