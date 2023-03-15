from django import template

from lemarche.cms.snippets import Advert


register = template.Library()


# Advert snippets
@register.inclusion_tag("cms/snippets/_advert_snippet.html", takes_context=True)
def cms_advert(context, layout="horizontal"):
    advert = Advert.objects.first()
    return {
        "advert": advert,
        "request": context["request"],
        "layout": layout,
    }
