from lemarche.siaes.models import Siae


SIAE_FIELDS_TO_EXPORT = [
    "name",
    "brand",
    "slug",
    "siret",  # siret_pretty ?
    "nature",
    "kind",
    "presta_type",
    "contact_website",
    # "contact_email",
    # "contact_phone",
    "address",
    "city",
    "post_code",
    "department",
    "region",
    "is_qpv",
    "sectors",
]
SIAE_CUSTOM_FIELDS = ["Inscrite"]
SIAE_HEADER = [
    Siae._meta.get_field(field_name).verbose_name for field_name in SIAE_FIELDS_TO_EXPORT
] + SIAE_CUSTOM_FIELDS


def generate_siae_row(siae: Siae):
    siae_row = []
    for field_name in SIAE_FIELDS_TO_EXPORT + SIAE_CUSTOM_FIELDS:
        # Improve display of some fields: ChoiceFields, BooleanFields, ArrayFields, ManyToManyFields
        if field_name in ["nature"]:
            siae_row.append(getattr(siae, f"get_{field_name}_display")())
        elif field_name in ["presta_type"]:
            siae_row.append(siae.presta_type_display)
        elif field_name in ["is_qpv"]:
            siae_row.append("Oui" if getattr(siae, field_name, None) else "Non")
        elif field_name == "sectors":
            siae_row.append(siae.sectors_list_to_string())
        elif field_name == "Inscrite":
            siae_row.append("Oui" if siae.user_count else "Non")
        else:
            siae_row.append(getattr(siae, field_name, ""))
    return siae_row
