"""
Dry-run : aperçu de ce que la migration nh3 ferait sur les besoins clôturés.

Usage (depuis la racine du projet, avec Django configuré) :
    python manage.py shell < scripts/check_nh3_sanitization.py
    # ou
    DJANGO_SETTINGS_MODULE=config.settings.dev python scripts/check_nh3_sanitization.py

Affiche uniquement les besoins dont le contenu serait modifié.
Ne touche à rien en base.
"""

import os
import sys
from datetime import date

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


def run():
    qs = Tender.objects.filter(
        deadline_date__isnull=False,
        deadline_date__lt=date.today(),
    ).only("id", "title", "description", "constraints")

    total = qs.count()
    affected_desc = []
    affected_constr = []

    for tender in qs.iterator(chunk_size=500):
        if tender.description:
            sanitized = sanitize_html(tender.description)
            if sanitized != tender.description:
                affected_desc.append(
                    {
                        "id": tender.id,
                        "title": tender.title,
                        "diff": diff_summary(tender.description, sanitized),
                    }
                )

        if tender.constraints:
            sanitized = sanitize_html(tender.constraints)
            if sanitized != tender.constraints:
                affected_constr.append(
                    {
                        "id": tender.id,
                        "title": tender.title,
                        "diff": diff_summary(tender.constraints, sanitized),
                    }
                )

    print(f"\n{'=' * 60}")
    print(f"Besoins clôturés analysés : {total}")
    print(f"Descriptions modifiées    : {len(affected_desc)} / {total}")
    print(f"Contraintes modifiées     : {len(affected_constr)} / {total}")
    print(f"{'=' * 60}\n")

    if affected_desc:
        print("── DESCRIPTIONS qui changeraient ──")
        for item in affected_desc:
            print(f"\n[#{item['id']}] {item['title']}")
            print(item["diff"])

    if affected_constr:
        print("\n── CONTRAINTES qui changeraient ──")
        for item in affected_constr:
            print(f"\n[#{item['id']}] {item['title']}")
            print(item["diff"])

    if not affected_desc and not affected_constr:
        print("✓ Aucun contenu ne serait modifié — l'allowlist est conforme.")


run()
