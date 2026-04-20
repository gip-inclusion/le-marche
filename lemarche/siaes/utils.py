from datetime import timedelta

from django.utils import timezone

from lemarche.siaes.models import Siae

NUDGE_FIELDS_MAX = 5
NUDGE_FIELD_STALE_MONTHS = 12


def calculate_etablissement_count(siae: Siae):
    if siae.siren:
        return Siae.objects.filter(is_active=True, siret__startswith=siae.siren).count()
    return 0


def get_nudge_fields(siae: Siae) -> list:
    """
    Return an ordered list of up to NUDGE_FIELDS_MAX fields to propose in the nudge module.

    Priority order:
    1. Empty inline fields (contact_email, ca, employees_insertion_count, employees_permanent_count)
    2. Stale inline fields (last updated > 12 months ago)
    3. Missing non-inline fields (sectors, client_references, labels) — link to dashboard
    """
    stale_threshold = timezone.now() - timedelta(days=NUDGE_FIELD_STALE_MONTHS * 30)
    fields = []

    # --- Priority 1: empty inline fields ---
    if not siae.contact_email:
        fields.append(
            {
                "field": "contact_email",
                "label": "Email du contact commercial",
                "value": "",
                "type": "email",
                "inline": True,
            }
        )
    if siae.ca is None:
        fields.append(
            {
                "field": "ca",
                "label": "Chiffre d'affaires annuel (€)",
                "value": "",
                "type": "number",
                "inline": True,
            }
        )
    if siae.employees_insertion_count is None:
        fields.append(
            {
                "field": "employees_insertion_count",
                "label": siae.etp_count_label_display,
                "value": "",
                "type": "number",
                "inline": True,
            }
        )
    if siae.employees_permanent_count is None:
        fields.append(
            {
                "field": "employees_permanent_count",
                "label": "Nombre de salariés permanents",
                "value": "",
                "type": "number",
                "inline": True,
            }
        )

    # --- Priority 2: stale inline fields (not already in list) ---
    existing = {f["field"] for f in fields}

    if "ca" not in existing and siae.ca is not None:
        if not siae.ca_last_updated or siae.ca_last_updated < stale_threshold:
            fields.append(
                {
                    "field": "ca",
                    "label": "Chiffre d'affaires annuel (€)",
                    "value": siae.ca,
                    "type": "number",
                    "inline": True,
                }
            )

    if "employees_insertion_count" not in existing and siae.employees_insertion_count is not None:
        if (
            not siae.employees_insertion_count_last_updated
            or siae.employees_insertion_count_last_updated < stale_threshold
        ):
            fields.append(
                {
                    "field": "employees_insertion_count",
                    "label": siae.etp_count_label_display,
                    "value": siae.employees_insertion_count,
                    "type": "number",
                    "inline": True,
                }
            )

    if "employees_permanent_count" not in existing and siae.employees_permanent_count is not None:
        if (
            not siae.employees_permanent_count_last_updated
            or siae.employees_permanent_count_last_updated < stale_threshold
        ):
            fields.append(
                {
                    "field": "employees_permanent_count",
                    "label": "Nombre de salariés permanents",
                    "value": siae.employees_permanent_count,
                    "type": "number",
                    "inline": True,
                }
            )

    # --- Priority 3: missing non-inline fields ---
    existing = {f["field"] for f in fields}

    if len(fields) < NUDGE_FIELDS_MAX and siae.sector_count == 0:
        fields.append(
            {
                "field": "sectors",
                "label": "Secteurs d'activité",
                "value": "",
                "type": "link",
                "inline": False,
            }
        )
    if len(fields) < NUDGE_FIELDS_MAX and siae.client_reference_count == 0:
        fields.append(
            {
                "field": "client_references",
                "label": "Références clients",
                "value": "",
                "type": "link",
                "inline": False,
            }
        )
    if len(fields) < NUDGE_FIELDS_MAX and siae.label_count == 0:
        fields.append(
            {
                "field": "labels",
                "label": "Labels & certifications",
                "value": "",
                "type": "link",
                "inline": False,
            }
        )

    return fields[:NUDGE_FIELDS_MAX]
