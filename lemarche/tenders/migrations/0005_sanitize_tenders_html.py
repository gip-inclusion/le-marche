from itertools import batched

from django.db import migrations

from lemarche.utils.sanitize import sanitize_html


BATCH_SIZE = 1_000


def sanitize_tenders(apps, schema_editor):
    """Sanitise les champs HTML rendus avec |safe sur tous les besoins.

    Applique la même allowlist que `sanitize_html` (utilisée à la saisie),
    pour garantir que la migration et l'assainissement runtime restent alignés.
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
                sanitized = sanitize_html(raw)
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
