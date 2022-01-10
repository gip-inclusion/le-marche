import xlwt

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


def export_siae_to_csv(csv_writer, siae_queryset):
    # header
    csv_writer.writerow(SIAE_HEADER)

    # rows
    for siae in siae_queryset:
        siae_row = generate_siae_row(siae)
        csv_writer.writerow(siae_row)

    return csv_writer


def export_siae_to_excel(siae_queryset):
    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Structures")

    row_number = 0

    # header
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    for (index, header_item) in enumerate(SIAE_HEADER):
        ws.write(row_number, index, header_item, font_style)
        # set column width
        # ws.col(col_num).width = HEADER[col_num][1]

    # rows
    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    for siae in siae_queryset:
        row_number += 1
        siae_row = generate_siae_row(siae)
        for (index, row_item) in enumerate(siae_row):
            ws.write(row_number, index, row_item, font_style)

    return wb
