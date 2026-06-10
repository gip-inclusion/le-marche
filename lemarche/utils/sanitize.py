import nh3


# Tags autorisés. Sur-ensemble de la toolbar CKEditor "frontuser"
# (Format, Bold, Italic, Underline, listes, Link) + balises structurelles
# sûres pour préserver le HTML plus riche envoyé par les partenaires (APProch).
_ALLOWED_TAGS = frozenset(
    {
        # texte / mise en forme
        "p",
        "br",
        "strong",
        "em",
        "u",
        "s",
        "sub",
        "sup",
        "blockquote",
        "pre",
        "code",
        "hr",
        # titres
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        # listes
        "ul",
        "ol",
        "li",
        # structure
        "div",
        "span",
        # tableaux
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "caption",
        # liens
        "a",
    }
)

# Attributs autorisés par tag
# - href, target sur <a> : préserve les liens CKEditor (target="_blank").
#   Le "rel" est géré par nh3 via link_rel (ajoute rel="noopener noreferrer"
#   automatiquement) ; l'autoriser explicitement ici lèverait une ValueError.
# - colspan/rowspan : préserve la structure des tableaux.
# Le "style" reste volontairement interdit (CSS non assaini = clickjacking,
# exfiltration via background-image, etc.).
_ALLOWED_ATTRIBUTES = {
    "a": {"href", "target"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
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
        return ""
    return nh3.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
    )
