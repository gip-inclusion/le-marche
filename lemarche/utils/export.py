import xlwt

from lemarche.siaes.models import Siae
from lemarche.utils.urls import get_share_url_object


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
SIAE_CONTACT_FIELDS = [
    "contact_first_name",
    "contact_last_name",
    "contact_email",
    "contact_phone",
    "contact_social_website",
]
SIAE_CUSTOM_FIELDS = ["Inscrite", "Lien vers le marché"]


def get_siae_fields(with_contact_info=False):
    siae_field_list = SIAE_FIELDS_TO_EXPORT
    if with_contact_info:
        siae_field_list += SIAE_CONTACT_FIELDS
    siae_field_list += SIAE_CUSTOM_FIELDS
    return siae_field_list


def generate_header(siae_field_list):
    header = []
    for field_name in siae_field_list:
        try:
            header.append(Siae._meta.get_field(field_name).verbose_name)
        except:  # noqa
            header.append(field_name)
    return header


def generate_siae_row(siae: Siae, siae_field_list):
    siae_row = []
    for field_name in siae_field_list:
        col_value = ""
        # Improve display of some fields
        # ChoiceFields
        if field_name in ["nature"]:
            col_value = getattr(siae, f"get_{field_name}_display")()
        # ArrayFields
        elif field_name in ["presta_type"]:
            col_value = siae.presta_type_display
        # BooleanFields
        elif field_name in ["is_qpv"]:
            col_value = "Oui" if getattr(siae, field_name, None) else "Non"
        # ManyToManyFields
        elif field_name == "sectors":
            col_value = siae.sectors_list_to_string()
        # Custom fields
        elif field_name == "Inscrite":
            col_value = "Oui" if siae.user_count else "Non"
        elif field_name == "Lien vers le marché":
            col_value = f"{get_share_url_object(siae)}?cmp=export-excel"
        else:
            col_value = getattr(siae, field_name, "")
        siae_row.append(col_value)
    return siae_row


def export_siae_to_csv(csv_writer, siae_queryset, with_contact_info=False):
    # columns
    field_list = get_siae_fields(with_contact_info)

    # header
    csv_writer.writerow(generate_header(field_list))

    # rows
    for siae in siae_queryset:
        siae_row = generate_siae_row(siae, field_list)
        csv_writer.writerow(siae_row)

    return csv_writer


def export_siae_to_excel(siae_queryset, with_contact_info=False):
    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Structures")

    row_number = 0

    # columns
    field_list = get_siae_fields(with_contact_info)

    # header
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    for (index, header_item) in enumerate(generate_header(field_list)):
        ws.write(row_number, index, header_item, font_style)
        # set column width
        # ws.col(col_num).width = HEADER[col_num][1]

    # rows
    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    for siae in siae_queryset:
        row_number += 1
        siae_row = generate_siae_row(siae, field_list)
        for (index, row_item) in enumerate(siae_row):
            ws.write(row_number, index, row_item, font_style)

    return wb
