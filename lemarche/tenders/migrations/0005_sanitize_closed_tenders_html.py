from datetime import date
from itertools import batched

import nh3
from django.db import migrations


ALLOWED_TAGS = frozenset({"p", "br", "strong", "em", "u", "ul", "ol", "li", "a", "h2", "h3", "h4"})
ALLOWED_ATTRIBUTES = {"a": {"href", "target", "rel"}}
ALLOWED_URL_SCHEMES = frozenset({"http", "https", "mailto"})

BATCH_SIZE = 1_000


def sanitize_closed_tenders(apps, schema_editor):
    """Sanitise les champs HTML des besoins clôturés (deadline_date passée).

    Ne touche pas aux besoins actifs (deadline dans le futur ou sans deadline).
    """
    Tender = apps.get_model("tenders", "Tender")

    qs = Tender.objects.filter(
        deadline_date__isnull=False,
        deadline_date__lt=date.today(),
    ).only("id", "description", "constraints")

    for batch in batched(qs.iterator(chunk_size=BATCH_SIZE), BATCH_SIZE):
        to_update = []
        for tender in batch:
            changed = False

            if tender.description:
                sanitized = nh3.clean(
                    tender.description,
                    tags=ALLOWED_TAGS,
                    attributes=ALLOWED_ATTRIBUTES,
                    url_schemes=ALLOWED_URL_SCHEMES,
                )
                if sanitized != tender.description:
                    tender.description = sanitized
                    changed = True

            if tender.constraints:
                sanitized = nh3.clean(
                    tender.constraints,
                    tags=ALLOWED_TAGS,
                    attributes=ALLOWED_ATTRIBUTES,
                    url_schemes=ALLOWED_URL_SCHEMES,
                )
                if sanitized != tender.constraints:
                    tender.constraints = sanitized
                    changed = True

            if changed:
                to_update.append(tender)

        if to_update:
            Tender.objects.bulk_update(to_update, ["description", "constraints"])


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0004_referentregional_logo"),
    ]

    operations = [
        migrations.RunPython(sanitize_closed_tenders, migrations.RunPython.noop),
    ]
