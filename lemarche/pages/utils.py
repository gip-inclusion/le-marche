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


def replace_page_content_strong(content):
    """
    on certain pages, we want to change the style of the <strong>text</strong>
    """
    content = content.replace(OPENING_STRONG, '<span class="text-important">')
    content = content.replace(CLOSING_STRONG, "</span>")

    return content
