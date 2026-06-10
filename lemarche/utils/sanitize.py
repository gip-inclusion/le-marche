import nh3


# Tags autorisés — alignés sur la toolbar CKEditor "frontuser"
# (Format, Bold, Italic, Underline, listes, Link)
_ALLOWED_TAGS = frozenset(
    {
        "p",
        "br",
        "strong",
        "em",
        "u",
        "ul",
        "ol",
        "li",
        "a",
        "h2",
        "h3",
        "h4",
    }
)

# Attributs autorisés par tag
# - href, target, rel sur <a> : préserve les liens CKEditor (target="_blank", rel="noopener")
_ALLOWED_ATTRIBUTES = {
    "a": {"href", "target", "rel"},
}

# Seuls ces schemes d'URL sont autorisés dans href
_ALLOWED_URL_SCHEMES = frozenset({"http", "https", "mailto"})


def sanitize_html(value: str) -> str:
    """Sanitise du HTML riche produit par CKEditor avant stockage.

    Préserve les balises de mise en forme légitimes et les liens (y compris
    target="_blank"). Neutralise tout script, iframe, gestionnaire d'événement
    et URL javascript:.
    Retourne une chaîne vide si value est None ou vide.
    """
    if not value:
        return value or ""
    return nh3.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
    )
