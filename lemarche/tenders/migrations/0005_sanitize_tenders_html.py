from itertools import batched

import nh3
from django.db import migrations


ALLOWED_TAGS = frozenset(
    {
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
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "div",
        "span",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "caption",
        "a",
    }
)
# "rel" est géré par nh3 (link_rel) ; l'autoriser ici lèverait une ValueError.
ALLOWED_ATTRIBUTES = {
    "a": {"href", "target"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
}
ALLOWED_URL_SCHEMES = frozenset({"http", "https", "mailto"})

BATCH_SIZE = 1_000


def sanitize_tenders(apps, schema_editor):
    """Sanitise les champs HTML rendus avec |safe sur tous les besoins.

    nh3 ne retire que le balisage dangereux (script, iframe, gestionnaires
    d'événements, URL javascript:) et préserve la mise en forme légitime, donc
    l'opération est sûre y compris sur les besoins actifs.
    """
    Tender = apps.get_model("tenders", "Tender")

    fields = ("description", "constraints")
    qs = Tender.objects.only("id", *fields)

    for batch in batched(qs.iterator(chunk_size=BATCH_SIZE), BATCH_SIZE):
        to_update = []
        for tender in batch:
            changed = False
            for field in fields:
                raw = getattr(tender, field)
                if not raw:
                    continue
                sanitized = nh3.clean(
                    raw,
                    tags=ALLOWED_TAGS,
                    attributes=ALLOWED_ATTRIBUTES,
                    url_schemes=ALLOWED_URL_SCHEMES,
                )
                if sanitized != raw:
                    setattr(tender, field, sanitized)
                    changed = True

            if changed:
                to_update.append(tender)

        if to_update:
            Tender.objects.bulk_update(to_update, fields)


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0004_referentregional_logo"),
    ]

    operations = [
        migrations.RunPython(sanitize_tenders, migrations.RunPython.noop),
    ]
