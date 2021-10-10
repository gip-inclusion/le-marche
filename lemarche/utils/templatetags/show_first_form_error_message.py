from django import template


register = template.Library()


@register.filter(name="show_first_form_error_message")
def show_first_form_error_message(form_errors_dict):
    try:
        return list(form_errors_dict.values())[0][0]
    except:  # noqa
        return ""
