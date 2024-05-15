from django import template

from lemarche.cms.snippets import InfoCard


register = template.Library()


# Advert snippets
@register.inclusion_tag("cms/snippets/_info_card_snippet.html", takes_context=True)
def cms_info_card(context):
    # we use only the last for now
    info_card = InfoCard.objects.last()
    return {
        "info_card": info_card,
        "request": context["request"],
    }
