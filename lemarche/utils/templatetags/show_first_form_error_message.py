from django import template


register = template.Library()


@register.filter(name="show_first_form_error_message")
def show_first_form_error_message(form_errors_dict):
    """
    Why would we use this template filter?
    - usually form errors display the form field name as key of the messsage, but we don't want to display it
    - we want to display only 1 form error at the time (or we know there's only 1 possible form error)
    """
    try:
        return list(form_errors_dict.values())[0][0]
    except:  # noqa
        return ""
