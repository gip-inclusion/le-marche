# flake8: noqa E203

OPENING_P = "<p>"
CLOSING_P = "</p>"
OPENING_STRONG = "<strong>"
CLOSING_STRONG = "</strong>"


def strip_page_content_surroundings_p(content):
    """
    by default, ckeditor adds "<p>" at the beginning and "</p>" at the end
    """
    if content[: (len(OPENING_P))] == OPENING_P:
        content = content[(len(OPENING_P)) :]

    if content[(-len(CLOSING_P)) :] == CLOSING_P:
        content = content[: (-len(CLOSING_P))]

    return content


def add_class_to_element(content, element="<strong>", class_to_add="", style_to_add=""):
    """
    on certain pages, we want to change the style of some elements
    """
    element_with_class_and_style = f'{element[:-1]} class="{class_to_add}" style="{style_to_add}">'
    content = content.replace(element, element_with_class_and_style)

    return content
