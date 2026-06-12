"""
Dry-run : aperçu de ce que la migration nh3 ferait sur les besoins.

Usage (depuis la racine du projet, avec Django configuré) :
    python manage.py shell < scripts/check_nh3_sanitization.py
    # ou
    DJANGO_SETTINGS_MODULE=config.settings.dev python scripts/check_nh3_sanitization.py

Affiche uniquement les besoins dont le contenu serait modifié.
Ne touche à rien en base.
"""

import os
import sys

import django


# Setup Django si lancé en standalone
if "django" not in sys.modules or not django.conf.settings.configured:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()

from lemarche.tenders.models import Tender  # noqa: E402
from lemarche.utils.sanitize import sanitize_html  # noqa: E402


def diff_summary(original: str, sanitized: str, max_len: int = 120) -> str:
    """Retourne un aperçu des différences (tronqué)."""
    if original == sanitized:
        return ""
    orig_short = original[:max_len].replace("\n", " ")
    sani_short = sanitized[:max_len].replace("\n", " ")
    return f"  AVANT : {orig_short}\n  APRÈS : {sani_short}"


FIELD_LABELS = {"description": "DESCRIPTIONS", "constraints": "CONTRAINTES"}


def run():
    fields = tuple(FIELD_LABELS)
    qs = Tender.objects.only("id", "title", *fields)

    total = 0
    affected = {field: [] for field in fields}

    for tender in qs.iterator(chunk_size=500):
        total += 1
        for field in fields:
            raw = getattr(tender, field)
            if not raw:
                continue
            sanitized = sanitize_html(raw)
            if sanitized != raw:
                affected[field].append({"id": tender.id, "title": tender.title, "diff": diff_summary(raw, sanitized)})

    print(f"\n{'=' * 60}")
    print(f"Besoins analysés          : {total}")
    print(f"Descriptions modifiées    : {len(affected['description'])} / {total}")
    print(f"Contraintes modifiées     : {len(affected['constraints'])} / {total}")
    print(f"{'=' * 60}\n")

    for field, label in FIELD_LABELS.items():
        if not affected[field]:
            continue
        print(f"\n── {label} qui changeraient ──")
        for item in affected[field]:
            print(f"\n[#{item['id']}] {item['title']}")
            print(item["diff"])

    if not any(affected.values()):
        print("✓ Aucun contenu ne serait modifié — l'allowlist est conforme.")


run()
