from lemarche.siaes.models import Siae


SIAE_FIELDS_TO_EXPORT = [
    "name",
    "brand",
    "siret",  # siret_pretty ?
    "nature",
    "kind",
    # "contact_email",
    # "contact_phone",
    # "contact_website",
    "city",
    "department",
    "region",
    "post_code",
    "is_qpv",
    "sectors",
]
SIAE_CUSTOM_FIELDS = ["Active"]
SIAE_HEADER = [
    Siae._meta.get_field(field_name).verbose_name for field_name in SIAE_FIELDS_TO_EXPORT
] + SIAE_CUSTOM_FIELDS


def generate_siae_row(siae: Siae):
    siae_row = []
    for field_name in SIAE_FIELDS_TO_EXPORT + SIAE_CUSTOM_FIELDS:
        # Improve display of some fields: ChoiceFields, BooleanFields, ManyToManyFields
        if field_name in ["nature"]:
            siae_row.append(getattr(siae, f"get_{field_name}_display")())
        elif field_name in ["is_qpv"]:
            siae_row.append("Oui" if getattr(siae, field_name, None) else "Non")
        elif field_name == "sectors":
            siae_row.append(siae.sectors_list_to_string())
        elif field_name == "Active":
            active = siae.users.exists()
            siae_row.append("Oui" if active else "Non")
        else:
            siae_row.append(getattr(siae, field_name, ""))
    return siae_row
